#include <cassert>
#include <cmath>
#include <string>
#include <tuple>
#include <vector>

#include <QDebug>
#include <QProcess>

#include "common/watchdog.h"
#include "common/util.h"
#include "selfdrive/ui/qt/network/networking.h"
#include "selfdrive/ui/qt/offroad/settings.h"
#include "selfdrive/ui/qt/qt_window.h"
#include "selfdrive/ui/qt/widgets/prime.h"
#include "selfdrive/ui/qt/widgets/scrollview.h"
#include "selfdrive/ui/qt/offroad/developer_panel.h"

TogglesPanel::TogglesPanel(SettingsWindow *parent) : ListWidget(parent) {
  // param, title, desc, icon
  std::vector<std::tuple<QString, QString, QString>> toggle_defs{
    {
      "OpenpilotEnabledToggle",
      tr("启用 openpilot"),
      tr("使用 openpilot 系统进行自适应巡航控制和车道保持辅助。使用此功能时需要始终保持注意力。更改此设置在车辆熄火后生效。"),
      "../assets/img_chffr_wheel.png",
    },
    {
      "ExperimentalLongitudinalEnabled",
      tr("openpilot 纵向控制 (Alpha)"),
      QString("<b>%1</b><br><br>%2")
        .arg(tr("警告: 此车辆的 openpilot 纵向控制功能处于 alpha 阶段，将会禁用自动紧急制动(AEB)。"))
        .arg(tr("在此车辆上，openpilot 默认使用车辆内置的 ACC 而不是 openpilot 的纵向控制。启用此选项将切换到 openpilot 纵向控制。启用 openpilot 纵向控制 alpha 版时建议同时启用实验模式。")),
      "../assets/offroad/icon_speed_limit.png",
    },
    {
      "ExperimentalMode",
      tr("实验模式"),
      "",
      "../assets/img_experimental_white.svg",
    },
    {
      "DisengageOnAccelerator",
      tr("踩油门时取消控制"),
      tr("启用后，踩下油门踏板将取消 openpilot 控制。"),
      "../assets/offroad/icon_disengage_on_accelerator.svg",
    },
    {
      "IsLdwEnabled",
      tr("启用车道偏离警告"),
      tr("当车速超过 50 km/h 且未打转向灯的情况下，如果车辆驶出检测到的车道线，系统将发出警告提醒您返回车道。"),
      "../assets/offroad/icon_warning.png",
    },
    {
      "AlwaysOnDM",
      tr("始终开启驾驶员监控"),
      tr("即使在 openpilot 未接管时也启用驾驶员监控。"),
      "../assets/offroad/icon_monitoring.png",
    },
    {
      "RecordFront",
      tr("记录并上传驾驶员摄像头"),
      tr("上传驾驶员摄像头数据，帮助改进驾驶员监控系统。"),
      "../assets/offroad/icon_monitoring.png",
    },
    {
      "IsMetric",
      tr("使用公制单位"),
      tr("使用公里/小时代替英里/小时显示速度。"),
      "../assets/offroad/icon_metric.png",
    },
  };

  std::vector longi_button_texts{tr("激进"), tr("标准"), tr("舒适"), tr("更舒适")};

  long_personality_setting = new ButtonParamControl(
    "LongitudinalPersonality",
    tr("驾驶风格"),
    tr("推荐使用标准模式。在激进模式下，openpilot 将与前车保持更近的距离，对油门和刹车的控制也更激进。在舒适模式下，openpilot 将与前车保持更远的距离。在支持的车型上，您可以通过方向盘上的距离按钮切换这些驾驶风格。"),
    "../assets/offroad/icon_speed_limit.png",
    longi_button_texts
  );

  // set up uiState update for personality setting
  QObject::connect(uiState(), &UIState::uiUpdate, this, &TogglesPanel::updateState);

  for (auto &[param, title, desc, icon] : toggle_defs) {
    auto toggle = new ParamControl(param, title, desc, icon, this);

    bool locked = params.getBool((param + "Lock").toStdString());
    toggle->setEnabled(!locked);

    addItem(toggle);
    toggles[param.toStdString()] = toggle;

    // insert longitudinal personality after NDOG toggle
    if (param == "DisengageOnAccelerator") {
      addItem(long_personality_setting);
    }
  }

  // Toggles with confirmation dialogs
  toggles["ExperimentalMode"]->setActiveIcon("../assets/img_experimental.svg");
  toggles["ExperimentalMode"]->setConfirmation(true, true);
}

void TogglesPanel::updateState(const UIState &s) {
  const SubMaster &sm = *(s.sm);

  if (sm.updated("selfdriveState")) {
    auto personality = sm["selfdriveState"].getSelfdriveState().getPersonality();
    if (personality != s.scene.personality && s.scene.started && isVisible()) {
      long_personality_setting->setCheckedButton(static_cast<int>(personality));
    }
    uiState()->scene.personality = personality;
  }
}

void TogglesPanel::expandToggleDescription(const QString &param) {
  toggles[param.toStdString()]->showDescription();
}

void TogglesPanel::showEvent(QShowEvent *event) {
  updateToggles();
}

void TogglesPanel::updateToggles() {
  auto experimental_mode_toggle = toggles["ExperimentalMode"];
  const QString e2e_description = QString("%1<br>"
                                        "<h4>%2</h4><br>"
                                        "%3<br>"
                                        "<h4>%4</h4><br>"
                                        "%5<br>")
                                .arg(tr("openpilot 默认使用<b>轻松模式</b>驾驶。实验模式启用了一些尚未准备好在轻松模式中使用的<b>alpha 级功能</b>。实验性功能如下："))
                                .arg(tr("端到端纵向控制"))
                                .arg(tr("让驾驶模型控制油门和刹车。openpilot 将像人类一样驾驶，包括在红灯和停车标志处停车。"
                                      "由于驾驶模型决定行驶速度，设定的巡航速度仅作为上限。这是一个 alpha 质量的功能；"
                                      "可能会出现错误。"))
                                .arg(tr("新的驾驶可视化"))
                                .arg(tr("在低速时，驾驶可视化将切换到道路朝向的广角摄像头以更好地显示某些转弯。实验模式标志也将显示在右上角。"));

  const bool is_release = params.getBool("IsReleaseBranch");
  auto cp_bytes = params.get("CarParamsPersistent");
  if (!cp_bytes.empty()) {
    AlignedBuffer aligned_buf;
    capnp::FlatArrayMessageReader cmsg(aligned_buf.align(cp_bytes.data(), cp_bytes.size()));
    cereal::CarParams::Reader CP = cmsg.getRoot<cereal::CarParams>();

    if (hasLongitudinalControl(CP)) {
      // normal description and toggle
      experimental_mode_toggle->setEnabled(true);
      experimental_mode_toggle->setDescription(e2e_description);
      long_personality_setting->setEnabled(true);
    } else {
      // no long for now
      experimental_mode_toggle->setEnabled(false);
      long_personality_setting->setEnabled(false);
      params.remove("ExperimentalMode");

      const QString unavailable = tr("由于使用了车辆原厂 ACC 进行纵向控制，此车型当前无法使用实验模式。");

      QString long_desc = unavailable + " " + \
                          tr("openpilot 纵向控制可能会在未来更新中提供。");
      if (CP.getExperimentalLongitudinalAvailable()) {
        if (is_release) {
          long_desc = unavailable + " " + tr("在非正式版本分支上可以测试 openpilot 纵向控制(alpha)和实验模式。");
        } else {
          long_desc = tr("启用 openpilot 纵向控制(alpha)开关以允许实验模式。");
        }
      }
      experimental_mode_toggle->setDescription("<b>" + long_desc + "</b><br><br>" + e2e_description);
    }

    experimental_mode_toggle->refresh();
  } else {
    experimental_mode_toggle->setDescription(e2e_description);
  }
}

DevicePanel::DevicePanel(SettingsWindow *parent) : ListWidget(parent) {
  setSpacing(50);
  addItem(new LabelControl(tr("设备 ID"), getDongleId().value_or(tr("未知"))));
  addItem(new LabelControl(tr("序列号"), params.get("HardwareSerial").c_str()));

  // power buttons
  QHBoxLayout *power_layout = new QHBoxLayout();
  power_layout->setSpacing(30);

  QPushButton *reboot_btn = new QPushButton(tr("重启"));
  reboot_btn->setObjectName("reboot_btn");
  power_layout->addWidget(reboot_btn);
  QObject::connect(reboot_btn, &QPushButton::clicked, this, &DevicePanel::reboot);

  QPushButton *poweroff_btn = new QPushButton(tr("关机"));
  poweroff_btn->setObjectName("poweroff_btn");
  power_layout->addWidget(poweroff_btn);
  QObject::connect(poweroff_btn, &QPushButton::clicked, this, &DevicePanel::poweroff);

  if (false && !Hardware::PC()) {
      connect(uiState(), &UIState::offroadTransition, poweroff_btn, &QPushButton::setVisible);
  }

  addItem(power_layout);

  QHBoxLayout* init_layout = new QHBoxLayout();
  init_layout->setSpacing(30);

  QPushButton* init_btn = new QPushButton(tr("拉取代码并重启"));
  init_btn->setObjectName("init_btn");
  init_layout->addWidget(init_btn);
  //QObject::connect(init_btn, &QPushButton::clicked, this, &DevicePanel::reboot);
  QObject::connect(init_btn, &QPushButton::clicked, [&]() {
    if (ConfirmationDialog::confirm(tr("确定要执行 Git pull 并重启吗？"), tr("确定"), this)) {

      QProcess process;
      process.start("git", QStringList() << "fetch");
      if (!process.waitForFinished()) {
        ConfirmationDialog::alert(tr("Git fetch 进程超时。"), this);
        return;
      }
      if (process.exitStatus() != QProcess::NormalExit) {
        ConfirmationDialog::alert(tr("Git fetch 进程崩溃。"), this);
        return;
      }
      if (process.exitCode() != 0) {
        ConfirmationDialog::alert(tr("获取更新失败。"), this);
        return;
      }

      // Git status to check if there are new updates
      process.start("git", QStringList() << "status" << "-uno");
      process.waitForFinished();

      QString output = process.readAllStandardOutput();
      if (output.isEmpty()) {
        ConfirmationDialog::alert(tr("无法读取 Git 状态。"), this);
        return;
      }
      if (!output.contains("Your branch is behind")) {
        ConfirmationDialog::alert(tr("已是最新版本。"), this);
        return;
      }

      // Git pull to apply updates
      process.start("git", QStringList() << "pull");
      process.waitForFinished();

      if (process.exitCode() != 0) {
        ConfirmationDialog::alert(tr("Git pull 失败。请检查日志。"), this);
        return;
      }

      ConfirmationDialog::alert(tr("Git pull 成功。正在重启..."), this);

      params.putBool("DoReboot", true);
    }
  });

  QPushButton* default_btn = new QPushButton(tr("恢复默认"));
  default_btn->setObjectName("default_btn");
  init_layout->addWidget(default_btn);
  //QObject::connect(default_btn, &QPushButton::clicked, this, &DevicePanel::poweroff);
  QObject::connect(default_btn, &QPushButton::clicked, [&]() {
    if (ConfirmationDialog::confirm(tr("确定要恢复默认设置吗？"), tr("确定"), this)) {
      //emit parent->closeSettings();
      QTimer::singleShot(1000, []() {
        printf("Set to default\n");
        Params().putInt("SoftRestartTriggered", 2);
        printf("Set to default2\n");
        });
    }
    });

  setStyleSheet(R"(
    #reboot_btn { height: 120px; border-radius: 15px; background-color: #2CE22C; }
    #reboot_btn:pressed { background-color: #24FF24; }
    #poweroff_btn { height: 120px; border-radius: 15px; background-color: #E22C2C; }
    #poweroff_btn:pressed { background-color: #FF2424; }
    #init_btn { height: 120px; border-radius: 15px; background-color: #2C2CE2; }
    #init_btn:pressed { background-color: #2424FF; }
    #default_btn { height: 120px; border-radius: 15px; background-color: #BDBDBD; }
    #default_btn:pressed { background-color: #A9A9A9; }
  )");
  addItem(init_layout);

  pair_device = new ButtonControl(
    tr("配对设备"),
    tr("配对"),
    tr("将您的设备与 comma connect (connect.comma.ai) 配对并获取您的 comma prime 优惠。")
  );
  connect(pair_device, &ButtonControl::clicked, [=]() {
    PairingPopup popup(this);
    popup.exec();
  });
  addItem(pair_device);

  // offroad-only buttons

  auto dcamBtn = new ButtonControl(
    tr("驾驶员摄像头"),
    tr("预览"),
    tr("预览面向驾驶员的摄像头以确保驾驶员监控视野良好。(车辆必须熄火)")
  );
  connect(dcamBtn, &ButtonControl::clicked, [=]() { emit showDriverView(); });
  addItem(dcamBtn);

  auto resetCalibBtn = new ButtonControl(tr("重置校准"), tr("重置"), "");
  connect(resetCalibBtn, &ButtonControl::showDescriptionEvent, this, &DevicePanel::updateCalibDescription);
  connect(resetCalibBtn, &ButtonControl::clicked, [&]() {
    if (ConfirmationDialog::confirm(tr("确定要重置校准吗？"), tr("重置"), this)) {
      params.remove("CalibrationParams");
      params.remove("LiveTorqueParameters");
      emit parent->closeSettings();
      QTimer::singleShot(1000, []() {
        Params().putInt("SoftRestartTriggered", 1);
      });
    }
  });
  addItem(resetCalibBtn);

  auto retrainingBtn = new ButtonControl(
    tr("查看培训指南"),
    tr("查看"),
    tr("查看 openpilot 的规则、功能和限制")
  );
  connect(retrainingBtn, &ButtonControl::clicked, [=]() {
    if (ConfirmationDialog::confirm(tr("确定要查看培训指南吗？"), tr("查看"), this)) {
      emit reviewTrainingGuide();
    }
  });
  addItem(retrainingBtn);

  if (Hardware::TICI()) {
    auto regulatoryBtn = new ButtonControl(tr("监管"), tr("查看"), "");
    connect(regulatoryBtn, &ButtonControl::clicked, [=]() {
      const std::string txt = util::read_file("../assets/offroad/fcc.html");
      ConfirmationDialog::rich(QString::fromStdString(txt), this);
    });
    addItem(regulatoryBtn);
  }

  auto translateBtn = new ButtonControl(tr("更改语言"), tr("更改"), "");
  connect(translateBtn, &ButtonControl::clicked, [=]() {
    QMap<QString, QString> langs = getSupportedLanguages();
    QString selection = MultiOptionDialog::getSelection(tr("选择语言"), langs.keys(), langs.key(uiState()->language), this);
    if (!selection.isEmpty()) {
      // put language setting, exit Qt UI, and trigger fast restart
      params.put("LanguageSetting", langs[selection].toStdString());
      qApp->exit(18);
      watchdog_kick(0);
    }
  });
  addItem(translateBtn);

  QObject::connect(uiState()->prime_state, &PrimeState::changed, [this] (PrimeState::Type type) {
    pair_device->setVisible(type == PrimeState::PRIME_TYPE_UNPAIRED);
  });
  QObject::connect(uiState(), &UIState::offroadTransition, [=](bool offroad) {
    for (auto btn : findChildren<ButtonControl *>()) {
      if (btn != pair_device) {
        btn->setEnabled(offroad);
      }
    }
    resetCalibBtn->setEnabled(true);
    translateBtn->setEnabled(true);
  });

}

void DevicePanel::updateCalibDescription() {
  QString desc = tr("openpilot 要求设备安装时左右偏差在 4° 以内，向上偏差在 5° 以内或向下偏差在 9° 以内。"
                   "openpilot 在持续校准中，很少需要重置。");
  std::string calib_bytes = params.get("CalibrationParams");
  if (!calib_bytes.empty()) {
    try {
      AlignedBuffer aligned_buf;
      capnp::FlatArrayMessageReader cmsg(aligned_buf.align(calib_bytes.data(), calib_bytes.size()));
      auto calib = cmsg.getRoot<cereal::Event>().getLiveCalibration();
      if (calib.getCalStatus() != cereal::LiveCalibrationData::Status::UNCALIBRATED) {
        double pitch = calib.getRpyCalib()[1] * (180 / M_PI);
        double yaw = calib.getRpyCalib()[2] * (180 / M_PI);
        desc += tr(" 您的设备向%1°%2 和 %3°%4倾斜。")
                    .arg(QString::number(std::abs(pitch), 'g', 1),
                         pitch > 0 ? tr("下") : tr("上"),
                         QString::number(std::abs(yaw), 'g', 1),
                         yaw > 0 ? tr("左") : tr("右"));
      }
    } catch (kj::Exception) {
      qInfo() << "invalid CalibrationParams";
    }
  }
  qobject_cast<ButtonControl *>(sender())->setDescription(desc);
}

void DevicePanel::reboot() {
  if (!uiState()->engaged()) {
    if (ConfirmationDialog::confirm(tr("确定要重启吗？"), tr("重启"), this)) {
      // Check engaged again in case it changed while the dialog was open
      if (!uiState()->engaged()) {
        params.putBool("DoReboot", true);
      }
    }
  } else {
    ConfirmationDialog::alert(tr("请先取消使能以重启"), this);
  }
}

void DevicePanel::poweroff() {
  if (!uiState()->engaged()) {
    if (ConfirmationDialog::confirm(tr("确定要关机吗？"), tr("关机"), this)) {
      // Check engaged again in case it changed while the dialog was open
      if (!uiState()->engaged()) {
        params.putBool("DoShutdown", true);
      }
    }
  } else {
    ConfirmationDialog::alert(tr("请先取消使能以关机"), this);
  }
}

void SettingsWindow::showEvent(QShowEvent *event) {
  setCurrentPanel(0);
}

void SettingsWindow::setCurrentPanel(int index, const QString &param) {
  panel_widget->setCurrentIndex(index);
  nav_btns->buttons()[index]->setChecked(true);
  if (!param.isEmpty()) {
    emit expandToggleDescription(param);
  }
}

SettingsWindow::SettingsWindow(QWidget *parent) : QFrame(parent) {

  // setup two main layouts
  sidebar_widget = new QWidget;
  QVBoxLayout *sidebar_layout = new QVBoxLayout(sidebar_widget);
  panel_widget = new QStackedWidget();

  // close button
  QPushButton *close_btn = new QPushButton(tr("×"));
  close_btn->setStyleSheet(R"(
    QPushButton {
      font-size: 140px;
      padding-bottom: 20px;
      border-radius: 100px;
      background-color: #292929;
      font-weight: 400;
    }
    QPushButton:pressed {
      background-color: #3B3B3B;
    }
  )");
  close_btn->setFixedSize(200, 200);
  sidebar_layout->addSpacing(45);
  sidebar_layout->addWidget(close_btn, 0, Qt::AlignCenter);
  QObject::connect(close_btn, &QPushButton::clicked, this, &SettingsWindow::closeSettings);

  // setup panels
  DevicePanel *device = new DevicePanel(this);
  QObject::connect(device, &DevicePanel::reviewTrainingGuide, this, &SettingsWindow::reviewTrainingGuide);
  QObject::connect(device, &DevicePanel::showDriverView, this, &SettingsWindow::showDriverView);

  TogglesPanel *toggles = new TogglesPanel(this);
  QObject::connect(this, &SettingsWindow::expandToggleDescription, toggles, &TogglesPanel::expandToggleDescription);

  auto networking = new Networking(this);
  QObject::connect(uiState()->prime_state, &PrimeState::changed, networking, &Networking::setPrimeType);

  QList<QPair<QString, QWidget *>> panels = {
    {tr("设备"), device},
    {tr("网络"), networking},
    {tr("开关"), toggles},
    {tr("软件"), new SoftwarePanel(this)},
    {tr("社区"), new CarrotPanel(this)},
    {tr("开发者"), new DeveloperPanel(this)},
  };

  nav_btns = new QButtonGroup(this);
  for (auto &[name, panel] : panels) {
    QPushButton *btn = new QPushButton(name);
    btn->setCheckable(true);
    btn->setChecked(nav_btns->buttons().size() == 0);
    btn->setStyleSheet(R"(
      QPushButton {
        color: grey;
        border: none;
        background: none;
        font-size: 65px;
        font-weight: 500;
      }
      QPushButton:checked {
        color: white;
      }
      QPushButton:pressed {
        color: #ADADAD;
      }
    )");
    btn->setSizePolicy(QSizePolicy::Preferred, QSizePolicy::Expanding);
    nav_btns->addButton(btn);
    sidebar_layout->addWidget(btn, 0, Qt::AlignRight);

    const int lr_margin = name != tr("网络") ? 50 : 0;  // Network panel handles its own margins
    panel->setContentsMargins(lr_margin, 25, lr_margin, 25);

    ScrollView *panel_frame = new ScrollView(panel, this);
    panel_widget->addWidget(panel_frame);

    QObject::connect(btn, &QPushButton::clicked, [=, w = panel_frame]() {
      btn->setChecked(true);
      panel_widget->setCurrentWidget(w);
    });
  }
  sidebar_layout->setContentsMargins(50, 50, 100, 50);

  // main settings layout, sidebar + main panel
  QHBoxLayout *main_layout = new QHBoxLayout(this);

  sidebar_widget->setFixedWidth(500);
  main_layout->addWidget(sidebar_widget);
  main_layout->addWidget(panel_widget);

  setStyleSheet(R"(
    * {
      color: white;
      font-size: 50px;
    }
    SettingsWindow {
      background-color: black;
    }
    QStackedWidget, ScrollView {
      background-color: #292929;
      border-radius: 30px;
    }
  )");
}


#include <QScroller>
#include <QListWidget>

static QStringList get_list(const char* path) {
  QStringList stringList;
  QFile textFile(path);
  if (textFile.open(QIODevice::ReadOnly)) {
    QTextStream textStream(&textFile);
    while (true) {
      QString line = textStream.readLine();
      if (line.isNull()) {
        break;
      } else {
        stringList.append(line);
      }
    }
  }
  return stringList;
}

CarrotPanel::CarrotPanel(QWidget* parent) : QWidget(parent) {
  main_layout = new QStackedLayout(this);
  homeScreen = new QWidget(this);
  carrotLayout = new QVBoxLayout(homeScreen);
  carrotLayout->setMargin(40);

  QHBoxLayout* select_layout = new QHBoxLayout();
  select_layout->setSpacing(30);


  QPushButton* start_btn = new QPushButton(tr("启动"));
  QPushButton* cruise_btn = new QPushButton(tr("巡航"));
  QPushButton* speed_btn = new QPushButton(tr("速度"));
  QPushButton* latLong_btn = new QPushButton(tr("调教"));
  QPushButton* disp_btn = new QPushButton(tr("显示"));
  QPushButton* path_btn = new QPushButton(tr("路径"));

  QString selected = QString::fromStdString(Params().get("CarSelected3"));
  QPushButton* selectCarBtn = new QPushButton(selected.length() > 1 ? selected : tr("选择您的车型"));

  if (selectedCar == "[ Not Selected ]") {
    Params().remove("CarSelected3");
  } else {
    printf(tr("已选择车型: %s\n").toStdString().c_str(), selectedCar.toStdString().c_str());
    Params().put("CarSelected3", selectedCar.toStdString());
    QTimer::singleShot(1000, []() {
      Params().putInt("SoftRestartTriggered", 1);
    });
    ConfirmationDialog::alert(selectedCar, this);
  }

  updateButtonStyles();

  select_layout->addWidget(start_btn);
  select_layout->addWidget(cruise_btn);
  select_layout->addWidget(speed_btn);
  select_layout->addWidget(latLong_btn);
  select_layout->addWidget(disp_btn);
  select_layout->addWidget(path_btn);
  carrotLayout->addLayout(select_layout, 0);

  QWidget* toggles = new QWidget();
  QVBoxLayout* toggles_layout = new QVBoxLayout(toggles);

  cruiseToggles = new ListWidget(this);
  cruiseToggles->addItem(new CValueControl("CruiseButtonMode", "巡航按钮模式", "0:普通,1:用户1,2:用户2", "../assets/offroad/icon_road.png", 0, 2, 1));
  cruiseToggles->addItem(new CValueControl("CruiseSpeedUnit", "巡航速度单位", "", "../assets/offroad/icon_road.png", 1, 20, 1));
  cruiseToggles->addItem(new CValueControl("CruiseEcoControl", "巡航: 节能控制(4km/h)", "临时提高设定速度以提高燃油效率", "../assets/offroad/icon_road.png", 0, 10, 1));
  cruiseToggles->addItem(new CValueControl("AutoSpeedUptoRoadSpeedLimit", "巡航: 自动加速 (0%)", "基于前车速度自动加速至道路限速", "../assets/offroad/icon_road.png", 0, 200, 10));
  cruiseToggles->addItem(new CValueControl("TFollowGap1", "跟车间距1: 跟车时间 (110)x0.01秒", "", "../assets/offroad/icon_road.png", 70, 300, 5));
  cruiseToggles->addItem(new CValueControl("TFollowGap2", "跟车间距2: 跟车时间 (120)x0.01秒", "", "../assets/offroad/icon_road.png", 70, 300, 5));
  cruiseToggles->addItem(new CValueControl("TFollowGap3", "跟车间距3: 跟车时间 (160)x0.01秒", "", "../assets/offroad/icon_road.png", 70, 300, 5));
  cruiseToggles->addItem(new CValueControl("TFollowGap4", "跟车间距4: 跟车时间 (180)x0.01秒", "", "../assets/offroad/icon_road.png", 70, 300, 5));
  cruiseToggles->addItem(new CValueControl("DynamicTFollow", "动态跟车间距控制", "", "../assets/offroad/icon_road.png", 0, 100, 5));
  cruiseToggles->addItem(new CValueControl("DynamicTFollowLC", "动态跟车间距控制 (变道时)", "", "../assets/offroad/icon_road.png", 0, 100, 5));
  cruiseToggles->addItem(new CValueControl("MyDrivingMode", "驾驶模式: 选择", "1:节能,2:安全,3:普通,4:高性能", "../assets/offroad/icon_road.png", 1, 4, 1));
  cruiseToggles->addItem(new CValueControl("MyDrivingModeAuto", "驾驶模式: 自动", "仅普通模式", "../assets/offroad/icon_road.png", 0, 1, 1));
  cruiseToggles->addItem(new CValueControl("TrafficLightDetectMode", "红绿灯检测模式", "0:关闭, 1:仅停车, 2:停车和启动", "../assets/offroad/icon_road.png", 0, 2, 1));
  cruiseToggles->addItem(new CValueControl("MaxAngleFrames", "最大转向角帧数(89)", "89:默认值, 转向仪表盘报错时设为85~87", "../assets/offroad/icon_logic.png", 80, 100, 1));
  cruiseToggles->addItem(new CValueControl("SteerActuatorDelay", "横向控制: 转向执行器延迟(40)", "标准", "../assets/offroad/icon_logic.png", 1, 100, 1));
  cruiseToggles->addItem(new CValueControl("LateralTorqueCustom", "LAT: TorqueCustom(0)", "", "../assets/offroad/icon_logic.png", 0, 2, 1));
  cruiseToggles->addItem(new CValueControl("LateralTorqueAccelFactor", "LAT: TorqueAccelFactor(2500)", "", "../assets/offroad/icon_logic.png", 1000, 6000, 10));
  cruiseToggles->addItem(new CValueControl("LateralTorqueFriction", "LAT: TorqueFriction(100)", "", "../assets/offroad/icon_logic.png", 0, 1000, 10));
  cruiseToggles->addItem(new CValueControl("CustomSteerMax", "LAT: CustomSteerMax(0)", "", "../assets/offroad/icon_logic.png", 0, 30000, 5));
  cruiseToggles->addItem(new CValueControl("CustomSteerDeltaUp", "LAT: CustomSteerDeltaUp(0)", "", "../assets/offroad/icon_logic.png", 0, 50, 1));
  cruiseToggles->addItem(new CValueControl("CustomSteerDeltaDown", "LAT: CustomSteerDeltaDown(0)", "", "../assets/offroad/icon_logic.png", 0, 50, 1));

  dispToggles = new ListWidget(this);
  dispToggles->addItem(new CValueControl("ShowDebugUI", "显示: 调试信息", "", "../assets/offroad/icon_shell.png", 0, 2, 1));
  dispToggles->addItem(new CValueControl("ShowDateTime", "显示: 时间信息",
    "0:无,1:时间和日期,2:仅时间,3:仅日期,4:时间和星期", "../assets/offroad/icon_calendar.png", 0, 4, 1));
  dispToggles->addItem(new CValueControl("ShowPathEnd", "显示: 路径终点", "0:不显示,1:显示", "../assets/offroad/icon_shell.png", 0, 1, 1));
  dispToggles->addItem(new CValueControl("ShowLaneInfo", "显示: 车道信息", "-1:无, 0:路径, 1:路径+车道, 2:路径+车道+路缘", "../assets/offroad/icon_shell.png", -1, 2, 1));
  dispToggles->addItem(new CValueControl("ShowRadarInfo", "显示: 雷达信息", "0:无,1:显示,2:相对位置,3:停止的车辆", "../assets/offroad/icon_shell.png", 0, 3, 1));
  dispToggles->addItem(new CValueControl("ShowRouteInfo", "显示: 路线信息", "0:不显示,1:显示", "../assets/offroad/icon_shell.png", 0, 1, 1));
  dispToggles->addItem(new CValueControl("ShowPlotMode", "显示: 调试图表", "", "../assets/offroad/icon_shell.png", 0, 10, 1));
  dispToggles->addItem(new CValueControl("ShowCustomBrightness", "亮度调节", "", "../assets/offroad/icon_brightness.png", 0, 100, 10));

  pathToggles = new ListWidget(this);
  pathToggles->addItem(new CValueControl("ShowPathModeCruiseOff", "显示: 路径模式: 巡航关闭", "0:普通,1,2:记录,3,4:^^,5,6:记录,7,8:^^,9,10,11,12:平滑^^", "../assets/offroad/icon_shell.png", 0, 15, 1));
  pathToggles->addItem(new CValueControl("ShowPathColorCruiseOff", "显示: 路径颜色: 巡航关闭", "(+10:Stroke)0:Red,1:Orange,2:Yellow,3:Green,4:Blue,5:Indigo,6:Violet,7:Brown,8:White,9:Black", "../assets/offroad/icon_shell.png", 0, 19, 1));
  pathToggles->addItem(new CValueControl("ShowPathMode", "显示: 路径模式: 无车道", "0:普通,1,2:记录,3,4:^^,5,6:记录,7,8:^^,9,10,11,12:平滑^^", "../assets/offroad/icon_shell.png", 0, 15, 1));
  pathToggles->addItem(new CValueControl("ShowPathColor", "显示: 路径颜色: 无车道", "(+10:Stroke)0:Red,1:Orange,2:Yellow,3:Green,4:Blue,5:Indigo,6:Violet,7:Brown,8:White,9:Black", "../assets/offroad/icon_shell.png", 0, 19, 1));
  pathToggles->addItem(new CValueControl("ShowPathModeLane", "显示: 路径模式: 车道模式", "0:普通,1,2:记录,3,4:^^,5,6:记录,7,8:^^,9,10,11,12:平滑^^", "../assets/offroad/icon_shell.png", 0, 15, 1));
  pathToggles->addItem(new CValueControl("ShowPathColorLane", "显示: 路径颜色: 车道模式", "(+10:Stroke)0:Red,1:Orange,2:Yellow,3:Green,4:Blue,5:Indigo,6:Violet,7:Brown,8:White,9:Black", "../assets/offroad/icon_shell.png", 0, 19, 1));
  pathToggles->addItem(new CValueControl("ShowPathWidth", "显示: 路径宽度比例(100%)", "", "../assets/offroad/icon_shell.png", 10, 200, 10));

  startToggles = new ListWidget(this);
  startToggles->addItem(selectCarBtn);
  startToggles->addItem(new ParamControl("HyundaiCameraSCC", "现代: 摄像头 SCC", "将 SCC 的 CAN 线连接到摄像头", "../assets/offroad/icon_shell.png", this));
  startToggles->addItem(new ParamControl("EnableRadarTracks", "启用雷达跟踪", "", "../assets/offroad/icon_shell.png", this));
  startToggles->addItem(new ParamControl("CanfdHDA2", "CANFD: HDA2 模式", "", "../assets/offroad/icon_shell.png", this));
  startToggles->addItem(new CValueControl("AutoCruiseControl", "自动巡航控制", "软停车，自动巡航开关控制", "../assets/offroad/icon_road.png", 0, 3, 1));
  startToggles->addItem(new CValueControl("CruiseOnDist", "巡航: 自动开启距离(0cm)", "当松开油门/刹车时，前车距离接近时自动开启巡航", "../assets/offroad/icon_road.png", 0, 2500, 50));
  startToggles->addItem(new CValueControl("AutoEngage", "启动时自动介入控制", "1:转向使能, 2:转向/巡航介入", "../assets/offroad/icon_road.png", 0, 2, 1));
  startToggles->addItem(new ParamControl("DisableMinSteerSpeed", "禁用最小转向速度", "", "../assets/offroad/icon_road.png", this));
  startToggles->addItem(new CValueControl("AutoGasTokSpeed", "自动加速速度", "加速使能速度", "../assets/offroad/icon_road.png", 0, 200, 5));
  startToggles->addItem(new ParamControl("AutoGasSyncSpeed", "自动更新巡航速度", "", "../assets/offroad/icon_road.png", this));
  startToggles->addItem(new CValueControl("SpeedFromPCM", "从 PCM 读取巡航速度", "丰田必须设为 1，本田设为 3", "../assets/offroad/icon_road.png", 0, 3, 1));
  startToggles->addItem(new CValueControl("SoundVolumeAdjust", "声音音量(100%)", "", "../assets/offroad/icon_sound.png", 5, 200, 5));
  startToggles->addItem(new CValueControl("SoundVolumeAdjustEngage", "介入提示音量(10%)", "", "../assets/offroad/icon_sound.png", 5, 200, 5));
  startToggles->addItem(new CValueControl("MaxTimeOffroadMin", "自动关机时间 (分钟)", "", "../assets/offroad/icon_sandtimer.png", 1, 600, 10));
  startToggles->addItem(new ParamControl("DisableDM", "禁用驾驶员监控", "", "../assets/img_driver_face_static_x.png", this));
  startToggles->addItem(new CValueControl("MapboxStyle", "地图样式(0)", "", "../assets/offroad/icon_shell.png", 0, 2, 1));
  startToggles->addItem(new CValueControl("RecordRoadCam", "记录道路摄像头(0)", "1:道路摄像头, 2:道路+广角摄像头", "../assets/offroad/icon_shell.png", 0, 2, 1));
  startToggles->addItem(new ParamControl("HotspotOnBoot", "开机启用热点", "", "../assets/offroad/icon_shell.png", this));
  startToggles->addItem(new CValueControl("NNFF", "NNFF", "Twilsonco 的 NNFF (需要重启)", "../assets/offroad/icon_road.png", 0, 1, 1));
  startToggles->addItem(new CValueControl("NNFFLite", "NNFFLite", "Twilsonco 的 NNFF-Lite (需要重启)", "../assets/offroad/icon_road.png", 0, 1, 1));

  speedToggles = new ListWidget(this);
  speedToggles->addItem(new CValueControl("AutoCurveSpeedLowerLimit", "弯道: 最低限速(30)", "遇到弯道时降低速度的最低限制", "../assets/offroad/icon_road.png", 30, 200, 5));
  speedToggles->addItem(new CValueControl("AutoCurveSpeedFactor", "弯道: 自动控制比例(100%)", "", "../assets/offroad/icon_road.png", 50, 300, 1));
  speedToggles->addItem(new CValueControl("AutoCurveSpeedAggressiveness", "弯道: 激进程度(100%)", "", "../assets/offroad/icon_road.png", 50, 300, 1));
  speedToggles->addItem(new CValueControl("AutoNaviSpeedCtrlEnd", "测速: 减速完成时间(6s)", "设置减速完成点，值越大离测速点越远", "../assets/offroad/icon_road.png", 3, 20, 1));
  speedToggles->addItem(new CValueControl("AutoNaviSpeedDecelRate", "测速: 减速率x0.01m/s^2(80)", "值越小从越远处开始减速", "../assets/offroad/icon_road.png", 10, 200, 10));
  speedToggles->addItem(new CValueControl("AutoNaviSpeedSafetyFactor", "测速: 安全系数(105%)", "", "../assets/offroad/icon_road.png", 80, 120, 1));
  speedToggles->addItem(new CValueControl("AutoNaviSpeedBumpTime", "减速带: 时间距离(1s)", "", "../assets/offroad/icon_road.png", 1, 50, 1));
  speedToggles->addItem(new CValueControl("AutoNaviSpeedBumpSpeed", "减速带: 通过速度(35km/h)", "", "../assets/offroad/icon_road.png", 10, 100, 5));
  speedToggles->addItem(new CValueControl("AutoNaviCountDownMode", "导航倒计时模式(2)", "0:关闭, 1:导航+测速, 2:导航+测速+减速带", "../assets/offroad/icon_road.png", 0, 2, 1));
  speedToggles->addItem(new CValueControl("TurnSpeedControlMode", "转弯速度控制模式(1)", "0:关闭, 1:视觉, 2:视觉+路线, 3:路线", "../assets/offroad/icon_road.png", 0, 3, 1));
  speedToggles->addItem(new CValueControl("MapTurnSpeedFactor", "地图转弯速度系数(100)", "", "../assets/offroad/icon_map.png", 50, 300, 5));
  speedToggles->addItem(new CValueControl("AutoTurnControl", "自动转向控制(0)", "0:无,1:变道,2:变道+速度,3:速度", "../assets/offroad/icon_road.png", 0, 3, 1));
  speedToggles->addItem(new CValueControl("AutoTurnControlSpeedTurn", "转向速度(20)", "0:无, 转向速度", "../assets/offroad/icon_road.png", 0, 100, 5));
  speedToggles->addItem(new CValueControl("AutoTurnControlTurnEnd", "转向控制距离时间(6)", "距离=速度*时间", "../assets/offroad/icon_road.png", 0, 30, 1));
  speedToggles->addItem(new CValueControl("AutoRoadSpeedAdjust", "自动道路限速调整(50%)", "", "../assets/offroad/icon_road.png", 0, 100, 10));
  speedToggles->addItem(new CValueControl("AutoTurnMapChange", "自动转向地图切换(0)", "", "../assets/offroad/icon_road.png", 0, 1, 1));

  toggles_layout->addWidget(cruiseToggles);
  toggles_layout->addWidget(dispToggles);
  toggles_layout->addWidget(pathToggles);
  toggles_layout->addWidget(startToggles);
  toggles_layout->addWidget(speedToggles);
  ScrollView* toggles_view = new ScrollView(toggles, this);
  carrotLayout->addWidget(toggles_view, 1);

  homeScreen->setLayout(carrotLayout);
  main_layout->addWidget(homeScreen);
  main_layout->setCurrentWidget(homeScreen);

  togglesCarrot(0);
}

void CarrotPanel::togglesCarrot(int widgetIndex) {
  startToggles->setVisible(widgetIndex == 0);
  cruiseToggles->setVisible(widgetIndex == 1);
  speedToggles->setVisible(widgetIndex == 2);
  latLongToggles->setVisible(widgetIndex == 3);
  dispToggles->setVisible(widgetIndex == 4);
  pathToggles->setVisible(widgetIndex == 5);
}

void CarrotPanel::updateButtonStyles() {
  QString styleSheet = R"(
      #start_btn, #cruise_btn, #speed_btn, #latLong_btn ,#disp_btn, #path_btn {
          height: 120px; border-radius: 15px; background-color: #393939;
      }
      #start_btn:pressed, #cruise_btn:pressed, #speed_btn:pressed, #latLong_btn:pressed, #disp_btn:pressed, #path_btn:pressed {
          background-color: #4a4a4a;
      }
  )";

  switch (currentCarrotIndex) {
  case 0:
      styleSheet += "#start_btn { background-color: #33ab4c; }";
      break;
  case 1:
      styleSheet += "#cruise_btn { background-color: #33ab4c; }";
      break;
  case 2:
      styleSheet += "#speed_btn { background-color: #33ab4c; }";
      break;
  case 3:
      styleSheet += "#latLong_btn { background-color: #33ab4c; }";
      break;
  case 4:
      styleSheet += "#disp_btn { background-color: #33ab4c; }";
      break;
  case 5:
      styleSheet += "#path_btn { background-color: #33ab4c; }";
      break;
  }

  setStyleSheet(styleSheet);
}


CValueControl::CValueControl(const QString& params, const QString& title, const QString& desc, const QString& icon, int min, int max, int unit)
    : AbstractControl(title, desc, icon), m_params(params), m_min(min), m_max(max), m_unit(unit) {

    label.setAlignment(Qt::AlignVCenter | Qt::AlignRight);
    label.setStyleSheet("color: #e0e879");
    hlayout->addWidget(&label);

    QString btnStyle = R"(
      QPushButton {
        padding: 0;
        border-radius: 50px;
        font-size: 35px;
        font-weight: 500;
        color: #E4E4E4;
        background-color: #393939;
      }
      QPushButton:pressed {
        background-color: #4a4a4a;
      }
    )";

    btnminus.setStyleSheet(btnStyle);
    btnplus.setStyleSheet(btnStyle);
    btnminus.setFixedSize(150, 100);
    btnplus.setFixedSize(150, 100);
    btnminus.setText("－");
    btnplus.setText("＋");
    hlayout->addWidget(&btnminus);
    hlayout->addWidget(&btnplus);

    connect(&btnminus, &QPushButton::released, this, &CValueControl::decreaseValue);
    connect(&btnplus, &QPushButton::released, this, &CValueControl::increaseValue);

    refresh();
}

void CValueControl::showEvent(QShowEvent* event) {
    AbstractControl::showEvent(event);
    refresh();
}

void CValueControl::refresh() {
    label.setText(QString::fromStdString(Params().get(m_params.toStdString())));
}

void CValueControl::adjustValue(int delta) {
    int value = QString::fromStdString(Params().get(m_params.toStdString())).toInt();
    value = qBound(m_min, value + delta, m_max);
    Params().putInt(m_params.toStdString(), value);
    refresh();
}

void CValueControl::increaseValue() {
    adjustValue(m_unit);
}

void CValueControl::decreaseValue() {
    adjustValue(-m_unit);
}
