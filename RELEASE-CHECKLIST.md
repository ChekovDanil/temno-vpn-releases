# Контрольный список релиза TEMNO VPN

## Для каждой платформы

- [ ] Версия и build number увеличены.
- [ ] Зафиксирован точный source commit.
- [ ] Пройдены автоматические и ручные проверки на чистом устройстве.
- [ ] Финальный файл подписан производственным ключом.
- [ ] SHA-256 и размер рассчитаны после подписи и упаковки.
- [ ] GitHub tag уникален, release asset больше не будет заменяться.
- [ ] URL содержит конкретный tag, а не `latest`.
- [ ] Checksum добавлен в `checksums/`.
- [ ] `latest.json` и платформенный манифест совпадают.
- [ ] Валидатор и unit-тесты проходят.

## Дополнительные ограничения

- [ ] Windows stable: Authenticode проверен на чистой Windows.
- [ ] Android: build type `release`, APK/AAB подписан production keystore.
- [ ] Android debug не загружен в GitHub Releases.
- [ ] iOS/iPadOS: TestFlight/App Store, публичного IPA нет.
- [ ] macOS: Developer ID, Hardened Runtime, notarization и stapling проверены.
- [ ] macOS: Gatekeeper запускает DMG/PKG без обходных команд.
- [ ] `automaticUpdate=true` используется только для подписанного stable-релиза
  после внедрения проверки подписи каталога и файла в клиенте.

