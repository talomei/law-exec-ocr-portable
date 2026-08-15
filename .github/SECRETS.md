# 🔐 GitHub Secrets 配置指南

> **目的**：让 GitHub Actions 自动签名 macOS / Windows 二进制
> **级别**：可选；不配也能跑构建，只是产物未签名

---

## 📋 总览

| 平台 | 是否需要 | 费用 | 申请周期 | 配置难度 |
|------|---------|------|----------|----------|
| **macOS** | 5 个 secrets | $99/年 | 1-3 天 | 🟡 中等 |
| **Windows EV** | 2 个 secrets | $300-500/年 | 3-7 天 | 🟢 简单 |
| **Windows Azure Trusted Signing** | 4 个 secrets | ~$10/月 | 1-3 天 | 🟢 简单 |

> 💡 **个人/小团队推荐路径**：
> - 短期：什么都不配 → 产物未签名 → 用户首次手动授权
> - 中期：买 macOS Developer ID（$99）→ 自动签名 macOS
> - 长期：加 Windows Azure Trusted Signing（$10/月）→ 自动签名 Windows

---

## 🍎 macOS 签名 + 公证（5 个 secrets）

### 前置：申请 Apple Developer ID

1. 访问 https://developer.apple.com/programs/enroll/
2. 选 **Individual**（个人）或 **Organization**（公司）
3. 付款 $99/年
4. 等 1-3 天审核通过
5. 审核通过后，访问 https://developer.apple.com/account 获取 **Team ID**（10 位字符）

### 申请 App-Specific Password

1. 访问 https://appleid.apple.com/account/manage
2. 登录 → **App-Specific Passwords** → **Generate Password**
3. 标签写 "GitHub Actions Notarization"
4. 记录生成的密码（一次性显示）

### 生成 Developer ID Application 证书

1. 在 Mac 上打开 **Keychain Access**
2. 菜单 **Keychain Access** → **Certificate Assistant** → **Request a Certificate From a Certificate Authority**
3. 填写：
   - User Email Address: 你的 Apple ID 邮箱
   - Common Name: 你的名字
   - CA Email Address: 留空
   - Request: **Saved to disk**
4. 保存 `CertificateSigningRequest.certSigningRequest` 到桌面
5. 访问 https://developer.apple.com/account/resources/certificates/list
6. 点 **+** → 选 **Developer ID Application** → 选 **Create**
7. 上传刚才的 CSR
8. 下载生成的 `developerID_application.cer`
9. 双击导入 Keychain
10. 在 Keychain Access 中找到 "Developer ID Application: ..."
11. 右键 → **Export** → 格式选 **Personal Information Exchange (.p12)**
12. 设置一个强密码（记住！）
13. 得到 `Certificates.p12` 文件

### 转换 P12 为 base64

```bash
# Mac / Linux
base64 -i Certificates.p12 -o cert.base64.txt

# Windows PowerShell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("Certificates.p12")) | Out-File -Encoding ASCII cert.base64.txt
```

整个 `cert.base64.txt` 文件内容（含换行）就是 secret 的值。

### 在 GitHub 上配置 Secrets

访问 https://github.com/你的用户名/law-exec-ocr-portable/settings/secrets/actions

点 **New repository secret**，依次添加：

| Secret 名 | 值 | 说明 |
|-----------|-----|------|
| `APPLE_ID` | 你的 Apple ID 邮箱 | 例如 user@icloud.com |
| `APPLE_TEAM_ID` | 10 位 Team ID | 在 developer.apple.com/account 顶部 |
| `APPLE_APP_SPECIFIC_PASSWORD` | 上一步生成的密码 | 16 位字符 |
| `MACOS_CERT_P12` | `cert.base64.txt` 全部内容 | base64 编码的 .p12 |
| `MACOS_CERT_PASSWORD` | 导出 .p12 时设的密码 | 记住的那个 |

### 验证

推一个 tag：
```bash
git tag v3.0.0-test
git push origin v3.0.0-test
```

进 Actions 页面看：
- 应该有 `Build macos-arm64` 和 `Build macos-x64` 两个 job
- 日志里搜 `notarytool submit`，看到 `Submitted`, `Accepted` 字样
- Release 页面下载 .zip，解压后 .app 应该能**直接双击**运行（无任何警告）

---

## 🪟 Windows 签名

### 方案 A：传统 EV 代码证书（$300-500/年）

#### 前置：购买证书

主流供应商：
- **DigiCert**：https://www.digicert.com/signing/code-signing-certificates.htm
- **Sectigo (Comodo)**：https://sectigo.com/ssl-certificates-tls/code-signing
- **GlobalSign**：https://www.globalsign.com/en/code-signing-certificate

#### 生成 PFX

1. 供应商会发你 .pfx 文件 + 密码（或给你工具生成）
2. 保存好这两个

#### 转换 PFX 为 base64

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("your_cert.pfx")) | Out-File -Encoding ASCII cert.base64.txt
```

#### 配置 GitHub Secrets

| Secret 名 | 值 |
|-----------|-----|
| `WINDOWS_CERT_PFX` | base64 编码的 .pfx 全部内容 |
| `WINDOWS_CERT_PASSWORD` | .pfx 密码 |

### 方案 B：Azure Trusted Signing（$10/月，更便宜）

**优势**：
- 不需要物理 USB 硬件令牌
- 费用低（~$10/月）
- 集成简单

**前置**：
1. Azure 订阅
2. 创建 Trusted Signing Account
3. 创建证书签名配置
4. 配置 GitHub Actions 的 OIDC 联邦

**配置 4 个 Secrets**：

| Secret 名 | 值 |
|-----------|-----|
| `AZURE_TENANT_ID` | Azure AD tenant ID |
| `AZURE_CLIENT_ID` | Service Principal client ID |
| `AZURE_CLIENT_SECRET` | Service Principal secret |
| `AZURE_SIGNING_ENDPOINT` | https://wus2.codesigning.azure.net |

> ⚠️ 当前 GitHub Actions 工作流用的是 signtool.exe（传统 PFX 方式）。如需 Azure Trusted Signing，需要修改 `.github/workflows/build-portable.yml` 的 Windows 签名步骤为 azure-sign-tool。

---

## 🧪 测试配置

### 1. 单独测某个平台

```bash
# 改代码后只跑 Windows 构建
# 编辑 .github/workflows/build-portable.yml，
# 在 strategy.matrix 下临时注释其他平台
```

### 2. 强制要求签名（构建失败时立即发现）

在 GitHub Actions 页面 → **Build Portable** → **Run workflow** → 勾选 **强制要求签名**。

如果 secrets 配错，build 会立即失败；不然会跳过签名默默产出未签名包。

### 3. 检查产物签名状态

```bash
# macOS
codesign -dv --verbose=4 LawExec-OCR.app
spctl -a -v LawExec-OCR.app    # 应显示 "accepted"

# Windows
signtool verify /pa LawExec-OCR.exe
# 应显示 "Successfully verified"
```

---

## 💰 成本对比

| 方案 | 首年 | 续费 | 体验 |
|------|------|------|------|
| **不签名** | $0 | $0 | 用户首次需手动授权 |
| **只签 macOS** | $99 | $99 | macOS 用户零障碍；Win 用户需点"仍要运行" |
| **macOS + Win EV** | $400-600 | $400-600 | 全平台零障碍 |
| **macOS + Win Azure** | $99 + $120 | $99 + $120 | 全平台零障碍，Win 不用 U 盾 |

**推荐组合**：
- 个人项目：**只签 macOS**（$99/年，律师同事主要是 Mac）
- 公司项目：**macOS + Win Azure**（$220/年）

---

## 🆘 常见问题

### Q1: PFX 文件 base64 后太大超 secret 限制

GitHub secret 单值上限 64 KB。PFX 一般 3-5 KB，base64 后 4-7 KB，远低于限制。

如果超了：
- 用 OpenSSL 重新生成更小的 PFX：`openssl pkcs12 -export -out new.pfx -inkey key.pem -in cert.pem`
- 或用更小的 EV 证书（某些供应商提供）

### Q2: macOS 公证失败 "App Store Connect operation failed"

通常是 App-Specific Password 错了。重新到 appleid.apple.com 生成一个。

### Q3: Windows signtool.exe 找不到

GitHub-hosted windows-latest 默认带 Windows SDK。如果用了 self-hosted runner，需要手动装：
```powershell
# 在 runner 上装 Windows SDK
winget install Microsoft.WindowsSDK.10.0.22621
```

### Q4: 签名后还是被 SmartScreen 拦

- EV 代码证书：首次拦截，但用户点"仍要运行"后**立即信任**（不再弹）
- 普通代码证书：永远拦截
- 解决：买 EV 证书

---

## 📚 参考资料

- [Apple notarytool 官方文档](https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution)
- [GitHub Actions OIDC for Azure](https://learn.microsoft.com/azure/active-directory/develop/workload-identity-federation)
- [Signtool.exe 文档](https://learn.microsoft.com/windows/win32/seccrypto/signtool)
- [Azure Trusted Signing](https://learn.microsoft.com/azure/trusted-signing/overview)

---

*📝 由 Claude Code 整理于 2026-08-15*
