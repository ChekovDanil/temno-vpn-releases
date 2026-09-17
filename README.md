# TEMNO VPN Releases

Официальный каталог пользовательских сборок TEMNO VPN. Здесь нет ключей
подписок, серверных конфигураций и пользовательских данных.

## Что доступно сейчас

| Платформа | Канал | Состояние |
| --- | --- | --- |
| Windows | beta | 0.9.12 RC: portable ZIP и тестовый неподписанный установщик |
| Android | internal | 0.2.0 debug только для локальной проверки, ссылки на скачивание нет |
| iOS/iPadOS | internal | проект в разработке, публичный IPA не предусмотрен |
| macOS | internal | подготовлен каркас прямой поставки, готового DMG пока нет |

[Windows 0.9.12 RC](https://github.com/ChekovDanil/temno-vpn-releases/releases/tag/windows-v0.9.12-rc)
предназначен для тестирования. Он не считается стабильным выпуском и не
устанавливается автоматически.

## Каналы

- `stable` — подписанные, проверенные пользовательские версии;
- `beta` — предварительные версии с неизменяемыми ссылками и SHA-256;
- `internal` — только состояние локальных сборок. В этом канале запрещены
  публичные ссылки на debug-файлы.

Главный каталог: [`updates/latest.json`](updates/latest.json). Для сайта и
клиентов сохраняется единая структура `channels → channel → platform`.
Платформенные представления находятся в `updates/windows.json`,
`updates/android.json`, `updates/ios.json` и `updates/macos.json`.

Все ссылки на бинарные файлы ведут на конкретный GitHub Release tag. Ссылки
вида `releases/latest/download/...` в каталог не допускаются: один URL всегда
должен означать один и тот же файл и один SHA-256.

## Проверка изменений

Перед каждым изменением каталога выполните:

```text
python scripts/validate_catalog.py
python -m unittest discover -s tests -v
```

Та же проверка автоматически запускается в GitHub Actions. Она блокирует:

- debug APK в `stable` и `beta`;
- прямую публикацию IPA;
- неподписанный, ненотарифицированный или не stapled DMG/PKG;
- изменяемые или посторонние URL;
- расхождение SHA-256 и файлов `checksums/*.txt`;
- расхождение главного и платформенных каталогов.

Подробный порядок выпуска описан в [DISTRIBUTION.md](DISTRIBUTION.md), а
контрольный список — в [RELEASE-CHECKLIST.md](RELEASE-CHECKLIST.md).
