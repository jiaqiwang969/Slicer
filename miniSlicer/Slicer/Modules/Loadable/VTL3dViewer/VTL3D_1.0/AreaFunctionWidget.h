/*
 * AreaFunctionWidget.h - Qt 重写版 AreaFunctionPicture 基础骨架
 * 仅实现空白绘制与 Data 单例引用，后续逐步补充曲线渲染逻辑。
 */
#pragma once

#include <QWidget>

class Data;        // 前向声明，避免头文件依赖
class VocalTract;  // 同上

class AreaFunctionWidget : public QWidget
{
  Q_OBJECT
public:
  explicit AreaFunctionWidget(QWidget *parent = nullptr);

  // 设置是否显示面积/周长、离散模式等开关，接口与旧 wx 类保持一致
  void setShowAreas(bool v) { m_showAreas = v; update(); }
  void setDiscrete(bool v) { m_discrete = v; update(); }

protected:
  void paintEvent(QPaintEvent *event) override;
  void resizeEvent(QResizeEvent *event) override;

private:
  void drawBackground(QPainter &p);
  void drawGraphs(QPainter &p);

private:
  bool m_showAreas {true};
  bool m_discrete  {false};
}; 