<div align="center">

# 💠 @jadegate/mcp-server

**JadeGate MCP 服务器 — AI Agent 技能的确定性安全验证。**

[![npm](https://img.shields.io/npm/v/@jadegate/mcp-server)](https://www.npmjs.com/package/@jadegate/mcp-server)
[![License: BSL-1.1](https://img.shields.io/badge/License-BSL%201.1-blue.svg)](https://github.com/JadeGate/jade-core/blob/main/LICENSE)

[English](./README.md)

</div>

## 这是什么？

一个 MCP（Model Context Protocol）服务器，将 [JadeGate](https://github.com/JadeGate/jade-core) 的安全验证能力暴露给 AI Agent 和 IDE（如 Claude Desktop、Cursor）。

JadeGate 提供 5 层确定性验证，纯本地运行，不联网，不调用 LLM，零 token 成本。

## 快速开始

```bash
npx @jadegate/mcp-server
```

或全局安装：

```bash
npm install -g @jadegate/mcp-server
jadegate-mcp
```

## 工具列表

| 工具 | 说明 |
|------|------|
| `jade_verify` | 验证技能 JSON — 返回 5 层验证结果、通过/失败状态和置信度分数 |
| `jade_search` | 按关键词、分类或信任等级搜索技能注册表 |
| `jade_info` | 根据技能 ID 获取详细信息 |
| `jade_list` | 列出所有已注册技能，支持分类过滤 |
| `jade_stats` | 获取注册表统计（技能总数、分类、信任分布） |
| `jade_dag` | 生成技能依赖图（Mermaid / D3 / DOT 格式） |

## 资源

| URI | 说明 |
|-----|------|
| `jadegate://registry` | 完整技能注册表（JSON） |
| `jadegate://ca` | JadeGate 根 CA 证书 |

## IDE 集成

### Claude Desktop

添加到 `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "jadegate": {
      "command": "npx",
      "args": ["-y", "@jadegate/mcp-server"]
    }
  }
}
```

### Cursor

添加到 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "jadegate": {
      "command": "npx",
      "args": ["-y", "@jadegate/mcp-server"]
    }
  }
}
```

## Python 替代方案

```bash
pip install jadegate
jade mcp-serve
```

同样的 MCP 协议，同样的工具 — 只是通过 Python 包运行。

## 工作原理

1. AI Agent 调用 `jade_verify` 传入技能 JSON
2. MCP 服务器调用 JadeGate 的 5 层验证管线
3. 返回确定性的通过/失败结果和详细的各层报告
4. Agent 根据结果决定是否信任并执行该技能

所有验证在本地运行，不联网，不调用 LLM，纯数学检查：
- Schema 校验
- 签名与来源验证
- 权限边界分析
- 依赖链审计
- 行为约束检查

## 环境要求

- Node.js >= 18
- JadeGate Python 包（`pip install jadegate`）需在 PATH 中可用

## 许可证

[BSL-1.1](https://github.com/JadeGate/jade-core/blob/main/LICENSE) — 详见 [jade-core](https://github.com/JadeGate/jade-core)。
