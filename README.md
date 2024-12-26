
What is openpilot?
------

[openpilot](http://github.com/commaai/openpilot) is an open source driver assistance system. Currently, openpilot performs the functions of Adaptive Cruise Control (ACC), Automated Lane Centering (ALC), Forward Collision Warning (FCW), and Lane Departure Warning (LDW) for a growing variety of [supported car makes, models, and model years](docs/CARS.md). In addition, while openpilot is engaged, a camera-based Driver Monitoring (DM) feature alerts distracted and asleep drivers. See more about [the vehicle integration](docs/INTEGRATION.md) and [limitations](docs/LIMITATIONS.md).

<table>
  <tr>
    <td><a href="https://youtu.be/NmBfgOanCyk" title="Video By Greer Viau"><img src="https://github.com/commaai/openpilot/assets/8762862/2f7112ae-f748-4f39-b617-fabd689c3772"></a></td>
    <td><a href="https://youtu.be/VHKyqZ7t8Gw" title="Video By Logan LeGrand"><img src="https://github.com/commaai/openpilot/assets/8762862/92351544-2833-40d7-9e0b-7ef7ae37ec4c"></a></td>
    <td><a href="https://youtu.be/SUIZYzxtMQs" title="A drive to Taco Bell"><img src="https://github.com/commaai/openpilot/assets/8762862/05ceefc5-2628-439c-a9b2-89ce77dc6f63"></a></td>
  </tr>
</table>

What is FrogPilot? 🐸
------

FrogPilot is a fully open-sourced fork of openpilot, featuring clear and concise commits striving to be a resource for the openpilot developer community. It thrives on contributions from both users and developers, focusing on a collaborative, community-led approach to deliver an advanced openpilot experience for everyone!

------
# 分支介绍文档

## 概述
本仓库包含多个分支，每个分支代表不同的功能或开发阶段。以下是每个主要分支的介绍，包括它们的用途和特点。

## 分支列表

### 1. `mazda-frogpilot`
- **功能描述**：该分支是 `MoreTore/openpilot` 仓库中的主要开发分支之一。它包含了为 Mazda 车型定制的功能和补丁，针对不同的硬件和软件环境进行了优化。
- **特点**：
  - 专门针对 Mazda 车型的 OpenPilot 配置。
  - 定期合并来自主仓库的更新。
  - 包括一些特定的调整和修复，以提高兼容性和性能。

### 2. `mazda-frogpilot-0.9.6`
- **功能描述**：`mazda-frogpilot-0.9.6` 是 `mazda-frogpilot` 分支的一个稳定版本，主要用于生产环境中的长期支持（LTS）版本。此版本包含了经过充分测试的功能，适合用于需要稳定性的场景。
- **特点**：
  - 版本号为 0.9.6，代表该分支处于一个较为稳定的状态。
  - 包括了与 `mazda-frogpilot` 相同的功能，但以稳定性为主，适合在长期使用中依赖。
  - 修复了一些已知问题和漏洞，提供了对旧版硬件的更好支持。

### 3. `FrogPilot`
- **功能描述**：`FrogPilot` 分支是来自 `frogai` 仓库的主要开发分支，包含了一些较为实验性的新功能和对 OpenPilot 框架的扩展。此分支较为前沿，适合用于开发和测试。
- **特点**：
  - 包含最新的实验功能和改进，适合用于 OpenPilot 框架的扩展和新功能的测试。
  - 比较前沿，可能包含不稳定的功能，不建议直接用于生产环境。
  - 定期进行功能改进和修复。

### 4. `FrogPilot-Development`
- **功能描述**：`FrogPilot-Development` 分支是 `frogai` 仓库中的开发版本，主要用于测试新特性和实验功能。它是 `FrogPilot` 分支的一个延伸，包含了更多的开发版本更新。
- **特点**：
  - 包含了对 `FrogPilot` 分支的进一步开发和实验功能。
  - 该分支可能不稳定，不适合直接投入生产使用。
  - 主要用于开发人员进行功能开发和测试。

### 5. `staging`
- **功能描述**：`staging` 分支是 `opgm/openpilot` 仓库中的预发布版本。此分支包含了一些待正式发布的特性和修复，通常会在发布前经过测试。
- **特点**：
  - 该分支包含了所有待发布的功能和修复，适合用于正式发布之前的最后阶段验证。
  - 包括了其他分支中的新特性，但这些特性经过了初步的测试。
  - 是发布过程中的过渡版本。

### 6. `carrot2-v6`
- **功能描述**：`carrot2-v6` 是 `ajouatom/openpilot` 仓库中的分支，针对特定硬件版本（如 Carrot 2 系列硬件）进行了优化。该分支包含了对硬件的兼容性调整和增强功能。
- **特点**：
  - 专为 `Carrot 2` 系列硬件设计，解决了与特定硬件的兼容性问题。
  - 包含了对硬件的优化和更新，适合用于特定硬件的部署。
  - 适合硬件开发人员和特定平台的用户。

## 分支同步与管理
所有分支都会定期与主仓库进行同步更新，确保它们与最新的代码库保持一致。下面是一些关键的同步步骤：

1. **同步 `mazda-frogpilot` 和 `mazda-frogpilot-0.9.6`**：
   - 每天同步来自 `MoreTore/openpilot` 仓库中的这两个分支，确保它们获得最新的 bug 修复和功能更新。
   - 删除任何可能存在的冲突分支，并推送到远程仓库。

2. **同步 `FrogPilot` 和 `FrogPilot-Development`**：
   - 从 `frogai` 仓库拉取最新的 `FrogPilot` 和 `FrogPilot-Development` 分支，并确保它们与主仓库保持同步。
   - 强制推送更新的分支，以确保没有遗漏的更改。

3. **同步 `staging` 和 `carrot2-v6`**：
   - 从 `opgm/openpilot` 和 `ajouatom/openpilot` 仓库同步 `staging` 和 `carrot2-v6` 分支，确保它们包含所有最新的稳定功能和硬件支持。
   - 对冲突的分支进行删除和重置，确保只有最新的版本。

## 结论
本仓库中的各个分支代表了不同的开发阶段和稳定性需求。通过同步这些分支，我们能够保持项目的最新进展，同时确保对不同硬件和功能的兼容性。请根据需求选择适合的分支进行开发和测试。
