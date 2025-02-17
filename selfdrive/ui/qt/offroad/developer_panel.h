#pragma once

#include "selfdrive/ui/qt/offroad/settings.h"
#include <string>

class DeveloperPanel : public ListWidget {
  Q_OBJECT
public:
  explicit DeveloperPanel(SettingsWindow *parent);
  void showEvent(QShowEvent *event) override;

private:
  Params params;
  ParamControl* adbToggle;
  ParamControl* joystickToggle;
  ParamControl* longManeuverToggle;
  ParamControl* experimentalLongitudinalToggle;
  ParamControl* cslcToggle;
  bool is_release;
  bool offroad;

private slots:
  void updateToggles(bool _offroad);
};
