#!/usr/bin/env python3
"""02_translate_with_openai.py
步骤 02：异步并发调用 OpenAI，读取 all_strings_tagged.txt（默认），分块翻译并生成 sed
脚本 replace.sh。与原 src/translate_ui_with_openai.py 内容一致，已内嵌在此文件中。
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import random
import sys
from pathlib import Path

import openai

# ---------------- Config -----------------
DEFAULT_MODEL = "gpt-4o-mini"
CHUNK_SIZE = 8_000            # 字符
CONCURRENCY = 200
MAX_RETRIES = 3
TIMEOUT = 120                 # s
BACKOFF_BASE = 2.0            # s
BACKOFF_JITTER = 0.25

LOG = logging.getLogger("ui-translator")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# -------------- helpers ------------------

def split_chunks(text: str, max_len: int):
    """按字符数切块，但保证 ###FILE: 段落完整"""
    blocks, cur, length = [], [], 0
    for line in text.splitlines(keepends=True):
        if line.startswith("###FILE:") and cur and length >= max_len:
            blocks.append("".join(cur))
            cur, length = [], 0
        cur.append(line)
        length += len(line)
    if cur:
        blocks.append("".join(cur))
    return blocks


async def call_openai(cli: openai.AsyncOpenAI, model: str, system_prompt: str, user_prompt: str) -> str:
    resp = await cli.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()


def backoff(n: int) -> float:
    base = BACKOFF_BASE * (2 ** (n - 1))
    return base * (1 + BACKOFF_JITTER * (2 * random.random() - 1))


async def worker(idx: int, queue: asyncio.Queue, cli: openai.AsyncOpenAI, cfg, fout):
    while True:
        item = await queue.get()
        if item is None:
            queue.task_done()
            break
        chunk_id, chunk_text = item
        for attempt in range(1, cfg.max_retries + 1):
            try:
                out = await asyncio.wait_for(call_openai(cli, cfg.model, cfg.system_prompt, chunk_text), TIMEOUT)
                async with fout_lock:
                    await fout.write(out + "\n")
                LOG.info("chunk %d processed by worker %d", chunk_id, idx)
                break
            except Exception as e:
                if attempt == cfg.max_retries:
                    LOG.error("chunk %d failed after %d attempts: %s", chunk_id, attempt, e)
                else:
                    await asyncio.sleep(backoff(attempt))
        queue.task_done()


# -------------- main ---------------------

def main():
    ap = argparse.ArgumentParser(description="调用 OpenAI 翻译并生成 sed 脚本")
    ap.add_argument("--big_file", default="all_strings_tagged.txt")
    ap.add_argument("--prompt_file", required=True)
    ap.add_argument("--output", default="replace.sh")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--base_url", default=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"))
    ap.add_argument("--chunk_size", type=int, default=CHUNK_SIZE)
    ap.add_argument("--concurrency", type=int, default=CONCURRENCY)
    ap.add_argument("--max_retries", type=int, default=MAX_RETRIES)
    args = ap.parse_args()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit("[ERR] 请先 export OPENAI_API_KEY")

    system_prompt = Path(args.prompt_file).read_text("utf-8")
    args.system_prompt = system_prompt  # attach to cfg for worker access
    big_text = Path(args.big_file).read_text("utf-8")

    chunks = split_chunks(big_text, args.chunk_size)
    LOG.info("total chunks: %d", len(chunks))

    cli = openai.AsyncOpenAI(api_key=api_key, base_url=args.base_url.rstrip("/"))

    queue: asyncio.Queue = asyncio.Queue()
    for i, c in enumerate(chunks):
        queue.put_nowait((i, c))
    for _ in range(args.concurrency):
        queue.put_nowait(None)

    async def run():
        async with aiofiles.open(args.output, "w", encoding="utf-8") as fout:
            global fout_lock
            fout_lock = asyncio.Lock()
            workers = [asyncio.create_task(worker(i, queue, cli, args, fout)) for i in range(args.concurrency)]
            await queue.join()
            for w in workers:
                w.cancel()

    import aiofiles  # lazy import after arg parse，避免非必须依赖影响 CLI 帮助
    asyncio.run(run())
    LOG.info("✅ 完成，已写 %s", args.output)


if __name__ == "__main__":
    main() 