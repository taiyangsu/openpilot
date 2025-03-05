#include <QDebug>
#include <QProcess>

#include "selfdrive/ui/qt/offroad/developer_panel.h"
#include "selfdrive/ui/qt/widgets/ssh_keys.h"
#include "selfdrive/ui/qt/widgets/controls.h"
#include "common/util.h"

DeveloperPanel::DeveloperPanel(SettingsWindow *parent) : ListWidget(parent) {
  adbToggle = new ParamControl("AdbEnabled", tr("Enable ADB"),
            tr("ADB (Android Debug Bridge) allows connecting to your device over USB or over the network. See https://docs.comma.ai/how-to/connect-to-comma for more info."), "");
  addItem(adbToggle);

  // SSH keys
  addItem(new SshToggle());
  addItem(new SshControl());

  joystickToggle = new ParamControl("JoystickDebugMode", tr("Joystick Debug Mode"), "", "");
  QObject::connect(joystickToggle, &ParamControl::toggleFlipped, [=](bool state) {
    params.putBool("LongitudinalManeuverMode", false);
    longManeuverToggle->refresh();
  });
  addItem(joystickToggle);

  longManeuverToggle = new ParamControl("LongitudinalManeuverMode", tr("Longitudinal Maneuver Mode"), "", "");
  QObject::connect(longManeuverToggle, &ParamControl::toggleFlipped, [=](bool state) {
    params.putBool("JoystickDebugMode", false);
    joystickToggle->refresh();
  });
  addItem(longManeuverToggle);

  cslcToggle = new ParamControl(
    "CSLCEnabled",
    tr("Cruise Speed Limit Control (CSLC)"),
    QString("<b>%1</b><br><br>%2")
      .arg(tr("Mazda车型自动控制车速功能"))
      .arg(tr("通过模拟按下巡航控制按钮来实现对车速的精确控制，使车辆能够自动跟随设定的目标速度。"
              "此功能依赖于车辆原厂巡航系统的可用性，速度调整精度受限于原厂巡航系统的调速精度。")),
    ""
  );
  if (!params.getBool("CSLCEnabled", false)) {
    params.putBool("CSLCEnabled", true);
  }
  addItem(cslcToggle);

  experimentalLongitudinalToggle = new ParamControl(
    "ExperimentalLongitudinalEnabled",
    tr("openpilot Longitudinal Control (Alpha)"),
    QString("<b>%1</b><br><br>%2")
      .arg(tr("WARNING: openpilot longitudinal control is in alpha for this car and will disable Automatic Emergency Braking (AEB)."))
      .arg(tr("On this car, openpilot defaults to the car's built-in ACC instead of openpilot's longitudinal control. "
              "Enable this to switch to openpilot longitudinal control. Enabling Experimental mode is recommended when enabling openpilot longitudinal control alpha.")),
    ""
  );
  experimentalLongitudinalToggle->setConfirmation(true, false);
  QObject::connect(experimentalLongitudinalToggle, &ParamControl::toggleFlipped, [=]() {
    updateToggles(offroad);
  });
  addItem(experimentalLongitudinalToggle);

  // Joystick and longitudinal maneuvers should be hidden on release branches
  is_release = params.getBool("IsReleaseBranch");

  // Toggles should be not available to change in onroad state
  QObject::connect(uiState(), &UIState::offroadTransition, this, &DeveloperPanel::updateToggles);
}

void DeveloperPanel::updateToggles(bool _offroad) {
  for (auto btn : findChildren<ParamControl *>()) {
    btn->setVisible(!is_release);

    /*
     * experimentalLongitudinalToggle should be toggelable when:
     * - visible, and
     * - during onroad & offroad states
     */
    if (btn != experimentalLongitudinalToggle && btn != cslcToggle) {
      btn->setEnabled(_offroad);
    }
  }

  // longManeuverToggle and experimentalLongitudinalToggle should not be toggleable if the car does not have longitudinal control
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
     * experimentalLongitudinalToggle should be visible when:
     * - is not a release branch, and
     * - the car supports experimental longitudinal control (alpha)
     */
    experimentalLongitudinalToggle->setVisible(CP.getExperimentalLongitudinalAvailable() && !is_release);

    // CSLC开关应该在Mazda车型上可见
    bool isMazda = CP.getCarName() == "mazda";
    cslcToggle->setVisible(isMazda && !is_release);
    // CSLC开关在行驶和停车状态下都可用
    cslcToggle->setEnabled(isMazda);

    longManeuverToggle->setEnabled(hasLongitudinalControl(CP) && _offroad);
  } else {
    longManeuverToggle->setEnabled(false);
    experimentalLongitudinalToggle->setVisible(false);
    cslcToggle->setVisible(false);
  }

  offroad = _offroad;
}

void DeveloperPanel::showEvent(QShowEvent *event) {
  updateToggles(offroad);

  // 确保CSLC功能默认开启
  if (!params.getBool("CSLCEnabled", false)) {
    params.putBool("CSLCEnabled", true);
    cslcToggle->refresh();
  }
}
