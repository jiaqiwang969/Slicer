#include "AreaFunctionWidget.h"

#include <QPainter>
#include <QPaintEvent>
#include "Data.h"      // 复用核心数据结构，后续可抽离到独立核心库

AreaFunctionWidget::AreaFunctionWidget(QWidget *parent)
  : QWidget(parent)
{
  // 启用 Qt 的自动刷新优化
  setAttribute(Qt::WA_OpaquePaintEvent);
  setAutoFillBackground(false);
  // 建议设定最小尺寸，避免被布局压扁
  setMinimumSize(400, 200);
}

void AreaFunctionWidget::paintEvent(QPaintEvent *event)
{
  QPainter p(this);
  p.setRenderHint(QPainter::Antialiasing);

  drawBackground(p);
  drawGraphs(p);

  QWidget::paintEvent(event); // 让 Qt 处理其他默认项
}

void AreaFunctionWidget::resizeEvent(QResizeEvent *event)
{
  QWidget::resizeEvent(event);
  // 未来若需要缓存 pixmap，可在此重新分配
}

void AreaFunctionWidget::drawBackground(QPainter &p)
{
  p.fillRect(rect(), Qt::white);
}

void AreaFunctionWidget::drawGraphs(QPainter &p)
{
  // 暂时绘制占位文字，证明 Qt Widget 正常渲染
  p.setPen(Qt::black);
  p.drawText(rect().adjusted(10, 10, -10, -10), Qt::AlignLeft | Qt::AlignTop,
             u8"AreaFunctionWidget (Qt 版) - TODO: 曲线渲染");

  // TODO: 从 Data::getInstance() 读取 vocalTract 曲线，绘制折线或柱状图
} 