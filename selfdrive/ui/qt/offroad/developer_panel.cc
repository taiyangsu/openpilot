#include <QDebug>
#include <QProcess>

#include "selfdrive/ui/qt/offroad/developer_panel.h"
#include "selfdrive/ui/qt/widgets/ssh_keys.h"
#include "selfdrive/ui/qt/widgets/controls.h"
#include "common/util.h"

DeveloperPanel::DeveloperPanel(SettingsWindow *parent) : ListWidget(parent) {
  adbToggle = new ParamControl("AdbEnabled", tr("启用 ADB"),
            tr("ADB (Android 调试桥)允许通过 USB 或网络连接到您的设备。更多信息请访问 https://docs.comma.ai/how-to/connect-to-comma"), "");
  addItem(adbToggle);

  // SSH 密钥
  addItem(new SshToggle());
  addItem(new SshControl());

  joystickToggle = new ParamControl("JoystickDebugMode", tr("游戏手柄调试模式"), "", "");
  QObject::connect(joystickToggle, &ParamControl::toggleFlipped, [=](bool state) {
    params.putBool("LongitudinalManeuverMode", false);
    longManeuverToggle->refresh();
  });
  addItem(joystickToggle);

  longManeuverToggle = new ParamControl("LongitudinalManeuverMode", tr("纵向操控模式"), "", "");
  QObject::connect(longManeuverToggle, &ParamControl::toggleFlipped, [=](bool state) {
    params.putBool("JoystickDebugMode", false);
    joystickToggle->refresh();
  });
  addItem(longManeuverToggle);

  experimentalLongitudinalToggle = new ParamControl(
    "ExperimentalLongitudinalEnabled",
    tr("openpilot 纵向控制 (测试版)"),
    QString("<b>%1</b><br><br>%2")
      .arg(tr("警告：此车型的 openpilot 纵向控制仍处于测试阶段，启用后将禁用自动紧急制动(AEB)。"))
      .arg(tr("在此车型上，openpilot 默认使用车辆内置的自适应巡航控制(ACC)而不是 openpilot 的纵向控制。"
              "启用此选项将切换到 openpilot 的纵向控制。启用 openpilot 纵向控制测试版时，建议同时启用实验模式。")),
    ""
  );
  experimentalLongitudinalToggle->setConfirmation(true, false);
  QObject::connect(experimentalLongitudinalToggle, &ParamControl::toggleFlipped, [=]() {
    updateToggles(offroad);
  });
  addItem(experimentalLongitudinalToggle);

  // 在正式发布版中应隐藏游戏手柄和纵向操控选项
  is_release = params.getBool("IsReleaseBranch");

  // 在行驶状态下不应允许更改开关状态
  QObject::connect(uiState(), &UIState::offroadTransition, this, &DeveloperPanel::updateToggles);
}

void DeveloperPanel::updateToggles(bool _offroad) {
  for (auto btn : findChildren<ParamControl *>()) {
    btn->setVisible(!is_release);

    /*
     * experimentalLongitudinalToggle 在以下情况下可切换：
     * - 可见时
     * - 在行驶和停车状态下
     */
    if (btn != experimentalLongitudinalToggle) {
      btn->setEnabled(_offroad);
    }
  }

  // 如果车辆不支持纵向控制，则不应允许切换 longManeuverToggle 和 experimentalLongitudinalToggle
  auto cp_bytes = params.get("CarParamsPersistent");
  if (!cp_bytes.empty()) {
    AlignedBuffer aligned_buf;
    capnp::FlatArrayMessageReader cmsg(aligned_buf.align(cp_bytes.data(), cp_bytes.size()));
    cereal::CarParams::Reader CP = cmsg.getRoot<cereal::CarParams>();

    if (!CP.getExperimentalLongitudinalAvailable() || is_release) {
      params.remove("ExperimentalLongitudinalEnabled");
      experimentalLongitudinalToggle->setEnabled(false);
    }

    /*
     * experimentalLongitudinalToggle 在以下情况下可见：
     * - 不是正式发布版本
     * - 车辆支持实验性纵向控制(测试版)
     */
    experimentalLongitudinalToggle->setVisible(CP.getExperimentalLongitudinalAvailable() && !is_release);

    longManeuverToggle->setEnabled(hasLongitudinalControl(CP) && _offroad);
  } else {
    longManeuverToggle->setEnabled(false);
    experimentalLongitudinalToggle->setVisible(false);
  }

  offroad = _offroad;
}

void DeveloperPanel::showEvent(QShowEvent *event) {
  updateToggles(offroad);
}