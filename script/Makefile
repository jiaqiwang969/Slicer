MODEL ?= gpt-4o-mini
CHUNK_SIZE ?= 8000
BASE_URL ?= https://ai.pumpkinai.online/v1

.PHONY: all translate clean monitor fix choose_rules step01 step02 step03 step04 step03-debug fix_xml_decl

.ONESHELL:

# 默认目标：执行一键翻译流水线
all: translate

translate: choose_rules step01 step02 step03 step04 fix_xml_decl

# ---------------- Step 01 ----------------
step01:
	@echo "---------------------------------------------"
	@echo "【Step01】生成占位符"
	@read -p "继续执行 Step01? (y/N) " ans; [ "$$ans" = "y" ] || (echo '已取消'; exit 1)
	@SEL=$(shell cat tmp_all/rules_sel.txt 2>/dev/null); \
	python 01_generate_placeholders.py \
	  --root ../miniSlicer \
	  --rules rules.yaml \
	  --rules_sel "$$SEL" \
	  --tmp_dir tmp_all \
	  --big_file tmp_all/all_strings_tagged.txt \
	  --map_file tmp_all/id_map.jsonl
	@python 01b_build_prompt.py \
	  --rules rules.yaml \
	  --used tmp_all/used_rules.txt \
	  --global prompt_global_header.txt \
	  --out tmp_all/auto_prompt.txt

# ---------------- Step 02 ----------------
step02:
	@echo "---------------------------------------------"
	@echo "【Step02】调用 LLM 翻译"
	@read -p "继续执行 Step02? (y/N) " ans; [ "$$ans" = "y" ] || (echo '已取消'; exit 1)
	@python 02_translate_with_openai.py \
	  --big_file tmp_all/all_strings_tagged.txt \
	  --prompt_file tmp_all/auto_prompt.txt \
	  --model ${MODEL} \
	  --chunk_size ${CHUNK_SIZE} \
	  --output tmp_all/replace.sh \
	  --base_url ${BASE_URL}

# ---------------- Step 03 ----------------
step03:
	@echo "---------------------------------------------"
	@echo "【Step03】写回中文"
	@read -p "继续执行 Step03? (y/N) " ans; [ "$$ans" = "y" ] || (echo '已取消'; exit 1)
	@python 03_apply_translations.py \
	  --tmp_dir tmp_all \
	  --sed_file tmp_all/replace.sh \
	  --dest_root ../miniSlicer \
	  --rules rules.yaml

# ---------------- Step 03 Debug ----------------
step03-debug:
	@echo "---------------------------------------------"
	@echo "【Step03-DEBUG】03_apply_translations.py 调试模式"
	@read -p "继续执行 Step03-DEBUG? (y/N) " ans; [ "$$ans" = "y" ] || (echo '已取消'; exit 1)
	@python 03_apply_translations.py \
	  --tmp_dir tmp_all \
	  --sed_file tmp_all/replace.sh \
	  --dest_root ../miniSlicer \
	  --rules rules.yaml \
	  --debug
	@echo "[Make] Step03-DEBUG 结束"

# ---------------- Step 04 ----------------
step04:
	@echo "---------------------------------------------"
	@echo "【Step04】清理占位符"
	@read -p "继续执行 Step04? (y/N) " ans; [ "$$ans" = "y" ] || (echo '已取消'; exit 1)
	@python 04_fix_placeholders.py --root ../miniSlicer --ext ui,xml,py,c,cpp,cxx,h,hpp
	@echo "[Make] 翻译流程完成"

clean:
	@echo "[Make] 清理临时文件…"
	@rm -rf tmp_all
	@echo "[Make] 完成清理"

monitor:
	@echo "[Make] 启动监控… 按 Ctrl+C 终止"
	@python 05-monitor-api.py

fix:
	@echo "[Make] 兜底清理占位符…"
	@python 04_fix_placeholders.py --root ../miniSlicer --ext ui,xml,py,c,cpp,cxx,h,hpp
	@echo "[Make] 完成清理"

choose_rules:
	@python choose_rules_helper.py

fix_xml_decl:
	@echo "[Make] 修复 XML 声明…"
	@python 06_fix_xml_decl.py --root ../miniSlicer
	@echo "[Make] XML 声明修复完毕"
