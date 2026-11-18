# Upstream UI first-import gate

The first commit containing FtShare_fincase UI must already show **QuantPilot** branding.
Never import an unchanged upstream page and promise to rebrand later.

1. Pin and document the upstream source commit.
2. Replace visible page title, logo, masthead, navigation, promotional banners and accessibility labels.
3. Remove original vendor marketing links, but preserve truthful identification of FtShare as the actual market-data provider.
4. Use QuantPilot-local browser storage keys and replace vendor-branded icons.
5. Preserve the original upstream MIT copyright and license notice in LICENSES/FTSHARE_FINCASE_LICENSE; keep the independent ECharts Apache-2.0 NOTICE/LICENSE when vendoring ECharts.
6. Keep test fixtures clearly labeled as simulated; do not distribute private production market-data exports or API keys.
7. Run python tools/check_brand.py, npm test, npm run build, pytest and inspect rendered UI.
8. Do not merge the upstream UI until all gates pass.

The initial API + quant_core scaffold does **not** import the upstream UI and is not evidence that UI migration has been completed.
