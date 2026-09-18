# TEMNO VPN Releases

Официальный каталог пользовательских сборок TEMNO VPN. Здесь нет ключей
подписок, серверных конфигураций и пользовательских данных.

## Что доступно сейчас

| Платформа | Канал | Состояние |
| --- | --- | --- |
| Windows | beta | 0.9.14 RC: portable ZIP и тестовый неподписанный установщик |
| Android | beta | 0.2.0 RC: три подписанных APK, ручная установка, без автообновления |
| iOS/iPadOS | internal | опубликован пакет исходников 0.4 для проверки интерфейса; готового VPN/IPA нет |
| macOS | internal | опубликован пакет исходников 0.4 для проверки интерфейса; готового DMG/VPN нет |

[Windows 0.9.14 RC](https://github.com/ChekovDanil/temno-vpn-releases/releases/tag/windows-v0.9.14-rc)
предназначен для тестирования. Он не считается стабильным выпуском и не
устанавливается автоматически.

[Android 0.2.0 RC](https://github.com/ChekovDanil/temno-vpn-releases/releases/tag/android-v0.2.0-rc)
содержит подписанные release APK для `arm64-v8a`, `armeabi-v7a` и `x86_64`.
Это предварительная ручная сборка: автоматическое обновление отключено, а
VPN-подключение на физическом Android-устройстве ещё не подтверждено.

[Apple handoff 0.4](https://github.com/ChekovDanil/temno-vpn-releases/releases/tag/apple-handoff-v0.4-internal)
содержит XcodeGen/SwiftUI-исходники и инструкции для проверки на Mac, iPhone и
iPad. Архив не является приложением: в нём нет готового рабочего Apple VPN,
Libbox.xcframework, подписанного и нотариализированного DMG или публичного IPA.

## Каналы

- `stable` — подписанные, проверенные пользовательские версии;
- `beta` — предварительные версии с неизменяемыми ссылками и SHA-256;
- `internal` — сведения о разработке и внутренних пакетах исходников. Этот
  канал не участвует в обновлениях; в нём запрещены ссылки на устанавливаемые
  debug-приложения. Допускается только явно помеченный архив исходников handoff.

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
- неподписанные Android APK и Android-кандидаты без полного перечня ABI;
- прямую публикацию IPA;
- неподписанный, ненотарифицированный или не stapled DMG/PKG;
- выдачу Apple handoff за готовое приложение или рабочий VPN;
- изменяемые или посторонние URL;
- расхождение SHA-256 и файлов `checksums/*.txt`;
- расхождение главного и платформенных каталогов.

Подробный порядок выпуска описан в [DISTRIBUTION.md](DISTRIBUTION.md), а
контрольный список — в [RELEASE-CHECKLIST.md](RELEASE-CHECKLIST.md).
