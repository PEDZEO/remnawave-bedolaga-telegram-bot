# Changelog

## [3.21.0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.20.0...v3.21.0) (2026-02-22)


### New Features

* **cabinet:** add menu layout stats endpoints ([4ea3c5f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4ea3c5f87e4562f40eb20bb7361f72e201953025))

## [3.20.0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.19.0...v3.20.0) (2026-02-22)


### New Features

* brand admin alerts for PEDZEO fork ([cec8257](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/cec82571866fbf6667395c024d8cf109b67e1efc))


### Bug Fixes

* avoid button click FK race on user lookup ([1f814a6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1f814a6cff2031a2ce788a6c9b2aded4e9d1d655))
* close async teardown leaks and re-enable unraisable checks ([3014332](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/301433227e7905c0a6764721daa269fb55e80780))
* fallback button click log to null user on FK conflict ([3982bd4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3982bd40b76074e86ebd3c467a2fccead2b32f9e))
* lock user row before button click stats insert ([818ac96](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/818ac960f612100236bf8a32ed0e277f30114064))
* log callback button stats without user FK dependency ([ee7be0f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ee7be0f7f1353fb78cb7a1cb8c6348bacc5eea67))
* **menu-layout:** apply cabinet button styles in layout mode ([ea10a2c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ea10a2c5b12b9c200021cead0fb10eef9b2ea282))
* **menu-layout:** disable style when section is off ([c08b458](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c08b458e6f80e56335ecc4f917d45af4f20c9eb6))
* point update notifications to PEDZEO repo ([564b07a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/564b07a60e9647f0f321b4bf6f07f731a79485d3))
* remap legacy alembic revision before upgrade ([e0f030e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e0f030e843be39a62f9ae512a18d8241e341fe76))
* stabilize tests and suppress legacy warning noise ([b873019](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b8730191a75541ca7fbdedecfdb3defb2111c9aa))


### Refactoring

* add explicit bootstrap service startup types ([1e5ab51](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1e5ab515e3f7c1733e540ab0827d44c573a122c4))
* add explicit return type for runtime logging setup ([41932d5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/41932d5740268ffbccbb3cbc28c27692453f71da))
* add explicit return type for top-level main ([34f270d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/34f270d020d21bf5332b699294b888fa17bbdc7c))
* align settings model_config with pydantic v2 API ([9144a4a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9144a4a01477b5b855d95377f83950565103b5cd))
* **bootstrap:** extract backup startup stage ([9f4a8dd](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9f4a8dde5102dd552741e371eb53dc9c37ac816f))
* **bootstrap:** extract bot setup stage ([b7aad31](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b7aad313e2ffada6147a2dabc0d6704a53a636fd))
* **bootstrap:** extract configuration loading stage ([938e27e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/938e27edad298e070e6bdcb11a2e90350597b96f))
* **bootstrap:** extract contest rotation startup stage ([3068c50](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3068c50f4d4166cc4f07a9e1e4823362656dafd4))
* **bootstrap:** extract core runtime startup pipeline ([8ba89a1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8ba89a1defd1745d189ee08bd436dc4908b1ce01))
* **bootstrap:** extract daily subscription startup stage ([c57ae80](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c57ae806b38551ad4d5b092bbd8cc6225c70a95f))
* **bootstrap:** extract database initialization stage ([2c5bb92](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2c5bb92ac7195480af51a0f74d0300d8e9cdf363))
* **bootstrap:** extract database migration startup stage ([6d7d2a4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6d7d2a4c2369f42f3aa685d268f8fae9a0f50ba2))
* **bootstrap:** extract entrypoint crash handling ([658a4ae](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/658a4ae54453ed177a1fc97e91449eee900ae62f))
* **bootstrap:** extract external admin startup stage ([8416b01](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8416b0156bff39be6203329c80050449cb5074d6))
* **bootstrap:** extract graceful signal handlers ([84b47f4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/84b47f473b85093c25e420d53253d76ee456b312))
* **bootstrap:** extract localization startup stage ([8074929](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/80749294291b919498a442e7ff38820e77abfdce))
* **bootstrap:** extract log rotation startup stage ([c6ecb4b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c6ecb4b4a2407257a3516ec59db60c62641eee17))
* **bootstrap:** extract maintenance startup stage ([5b9c53a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5b9c53a46e83a280cfb63dbaf738e9f524c9a58a))
* **bootstrap:** extract monitoring startup stage ([ed05eab](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ed05eabbb9237dad4ff8362a835a0de54471421c))
* **bootstrap:** extract nalogo queue startup stage ([6af3ba6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6af3ba66166e82073ebf4debd1d17539161441d0))
* **bootstrap:** extract payment methods startup stage ([7209097](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7209097cba82d0df0e6769409d3f5a03f1bcf900))
* **bootstrap:** extract payment runtime setup ([1c58232](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1c58232f511290707a0b6395677baa9ac97a1aec))
* **bootstrap:** extract payment verification startup stage ([62068c5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/62068c58f7d76afc830f731a5a2aa447810012d2))
* **bootstrap:** extract polling startup stage ([ebca928](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ebca92862ccc186870a04ba48fd12d2e8bbef7ba))
* **bootstrap:** extract referral contests startup stage ([a413cc8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a413cc8fdb9e948c110f62cce6d9a92adfd6ebce))
* **bootstrap:** extract remnawave sync startup stage ([4945448](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4945448ab85045bd47aa4777ee9ec90fa20878c4))
* **bootstrap:** extract reporting startup stage ([6835028](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/683502868f78008ffc7215be3646c43b9c195e27))
* **bootstrap:** extract runtime execution stage ([74e59e5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/74e59e5f4fa59a5e7d77e2cfcc5aefccf8d62271))
* **bootstrap:** extract runtime logging configuration ([9ce92d2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9ce92d285a9d1e041b9d08623ff5cd82c79cb723))
* **bootstrap:** extract runtime logging configuration ([c499f40](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c499f40d205950d73623f9c8cbc6906ed4f7aaa2))
* **bootstrap:** extract runtime mode resolution ([97d7e9b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/97d7e9bdfe049bf3ffdeb3cc80bc540b15f51a05))
* **bootstrap:** extract runtime services shutdown stage ([6c9df32](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6c9df32536673a830aa7905e1ac096bf7826e172))
* **bootstrap:** extract runtime tasks startup stage ([43aa907](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/43aa907f98b1636aec6c5f959557f42524475e4c))
* **bootstrap:** extract runtime watchdog loop ([532c9a8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/532c9a87d12936eb78b83db65a03e089ef98e326))
* **bootstrap:** extract server sync startup stage ([9bc7300](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9bc730027b87171fd3b813f8111a87ce11b7aa74))
* **bootstrap:** extract service wiring stages ([4893ebe](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4893ebee177fd018313b03963f95a17ab026922a))
* **bootstrap:** extract shutdown pipeline ([a8bef70](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a8bef7028ce2dd9a949166f2ab33d209a13eb3e9))
* **bootstrap:** extract startup finalize stage ([40ea967](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/40ea967d2016aa6278c56640ea95c389bdc04e90))
* **bootstrap:** extract startup notification sender ([09b4bf5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/09b4bf536999dea27012a311845b62d168e21d86))
* **bootstrap:** extract startup summary logging ([8142da7](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8142da78c839d5fe2d471914f4225870a9845396))
* **bootstrap:** extract tariff sync startup stage ([924278f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/924278f08585cf2a93cd22038229a478702b691e))
* **bootstrap:** extract telegram webhook startup stage ([284f05a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/284f05a07ba777fc64ad2519f5cd841aaba01a81))
* **bootstrap:** extract traffic monitoring startup stage ([812d1ef](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/812d1ef3f2cfb1b1c71bacc197c5c5cd11303bad))
* **bootstrap:** extract version check startup stage ([5c485c8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5c485c8bc3207dfa5d405ea55f7beaaad94a27b0))
* **bootstrap:** extract web server startup stage ([24f28a8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/24f28a897c2aced90b3ee4748376a9ea65a7d4bd))
* **bootstrap:** extract web shutdown stage ([569768c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/569768cb1287f2a91ecddae186fd245be3600ca0))
* **bootstrap:** tighten runtime typing contracts ([4b0ffca](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4b0ffcaf62c8a2285f9d74f1307105b0cbbbd464))
* centralize runtime state mappings ([3a036f5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3a036f5d99b62cb36f8a423cd67547680d9d5bfe))
* centralize runtime task assembly ([52bb959](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/52bb959312469b55ed7138447aced56bb065af54))
* centralize shutdown payload assembly ([b7629cb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b7629cb4ae4ba16d233f986069cffc8f543ee038))
* centralize startup summary payload mapping ([c273f8e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c273f8eab276e1fc54dd397c1af52b6b3cd1f113))
* complete startup stage error helper rollout ([c3462fc](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c3462fc2a76a59b025624ab6aaff8dca2e53045d))
* deduplicate core payment CRUD wrapper calls ([4630f0a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4630f0a78192c9b4aad72b63b1fcc36572f9189d))
* deduplicate runtime shutdown stop calls ([0cd70eb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0cd70eb3b20edafde68ad8e1cd69880eb11142bd))
* deduplicate runtime watchdog restart branches ([026bdf6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/026bdf6775e471f3073b355e7a9a55130772b5cd))
* extract alembic revision read helper in migration bridge ([62627ea](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/62627ea41f6721d14dcb0f919cc3bcab961a78a4))
* extract preflight runtime object builder ([00693bb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/00693bbd55a3d7499728395c57c709b34577372b))
* extract runtime preflight banner metadata builder ([499ff9a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/499ff9a328d46cc61a0a81903b233cb1c1fef977))
* extract runtime preflight bootstrap ([5c6a1ee](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5c6a1eef48cf9b0d5ee27a5a95a3e43d39162aae))
* extract runtime session flow ([26509f2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/26509f236efa327f74f2ea6e17e50eb504c0c398))
* extract runtime shutdown payload composer ([86c1e17](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/86c1e17cb1bd65e6b323f2b99e16ac69966c7406))
* extract startup runtime orchestration ([7f8ca2b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7f8ca2b44d0bc23633b6d8d7d14da274a7ebea1d))
* formalize core runtime mode flags contract ([0c6a711](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0c6a711fc87d80baf0751a150f86d8f9b25bb97d))
* generate payment CRUD compatibility wrappers ([e61bdc4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e61bdc48a1a22d8554b00939799b15237a9978f1))
* group guarded service shutdown calls ([a98127f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a98127f3a09bd08635449422c240b2feae129b12))
* isolate core runtime context assembly ([c8b45c0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c8b45c001baaf4a621e01ab90921d2e9bab001c0))
* isolate post-payment bootstrap sequence ([72a6bc4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/72a6bc4e4475cc852aeb0ca0680f19b5d1c2829b))
* isolate pre-runtime bootstrap sequence ([e484970](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e48497036b36221f10d3a92f75f452ddafb96d21))
* isolate runtime loop state handoff ([708662c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/708662c315797d475d661e8253be8710ed909472))
* isolate runtime orchestration task startup handoff ([c288a1a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c288a1a12b7a427668635cec8934cf20a1c821af))
* isolate runtime session shutdown finalization ([d026142](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d026142d6a6b290e2df1843c1447dbc0ce035abd))
* isolate runtime shutdown args builder ([edaec72](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/edaec727650910f47f1a67879f0931f0acd41513))
* isolate startup finalize args builder ([86012c0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/86012c06b200ed38a4563ffecdd74add6e212a03))
* isolate web shutdown args builder ([5821db5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5821db5d0c9cafceeb98a3347c20fdeaa0f054d1))
* isolate web startup bootstrap sequence ([bcf4361](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/bcf4361b3c570d0e174e57f5a274ae4f9c1d6ee8))
* **main:** extract runtime state container ([147b033](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/147b0331495a59ecb081c9d6f520295dda830671))
* **main:** remove locals check for bot shutdown ([e1d5748](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e1d57488f5c7e4a3b9f0db87d3321a9a2957fd55))
* migrate admin and webhook schemas to pydantic v2 config ([429f40b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/429f40be0cab6af78f7ec44946cd75de7cc838a5))
* migrate campaign schema validators to pydantic v2 ([6a19c5f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6a19c5f2c2571cb533ad20d29d922c56cd71408a))
* migrate common webapi validators to pydantic v2 ([0b0b449](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0b0b449dc0f1e7ef0a33623482d2faa17d0b5dcc))
* migrate core cabinet schemas to pydantic v2 config ([7ad8f0d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7ad8f0d834302c1ed622f29f0700dd5e5d6e5c4e))
* migrate promo and broadcast validators to pydantic v2 ([5a87908](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5a879081203feda9358827e3b2e14d4ec8ca5e1a))
* migrate remaining cabinet schemas to pydantic v2 config ([183eb67](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/183eb675cc52622e8b69dff892cfc97b3f3fc1c5))
* migrate unified app lifecycle to lifespan ([5ba3ea8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5ba3ea809f6a6f2df5703ad3494b2babaab9fb77))
* migrate webapi payload serialization to model_dump ([b54bb88](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b54bb88d3ac5d7fe7002725c0a3477558f541c20))
* reduce pydantic and async-test warning hotspots ([e841d72](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e841d727f17de56a5d9d2f9c86dd0d39a3cd1684))
* reuse startup error helper in service stages ([21bd8db](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/21bd8db938b11851822eb7a1a6b0b542180dc825))
* share startup stage error handling ([b6e2ed7](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b6e2ed7ed80bee827d1e54cdc9aa26addd1bd025))
* simplify migration startup flag handling ([328a6a8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/328a6a875dde0809d25a9f0c5675ec58afb2c543))
* simplify startup webhook summary assembly ([cb44fb9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/cb44fb948d31567ca23702952653d42034429fb9))
* split shutdown pipeline stage dispatch ([1a5ff6f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1a5ff6f421f3fa6c4072c8b8d54ac3ff83c77fbb))
* tighten bootstrap entrypoint coroutine contract ([78e1a34](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/78e1a341b4b4fc8f52f07df463adae31121984d6))
* tighten bootstrap logger and notifier protocols ([eff907d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/eff907df5c9782a78ba00dbb26645315fbf23331))
* tighten bootstrap web shutdown typing and pytest loop cleanup ([4d907ed](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4d907edea2b9ab2b536c587b6c61086e19fdb3c2))
* tighten runtime orchestration typing ([df59285](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/df592852ad955dee83bbb2192211d3c59a902a00))
* type bot and webhook bootstrap stages ([6827f7b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6827f7bf76c1dcb94329ac39cf7af1e2aa1b7bb2))
* type core bootstrap sync and migration stages ([0498b5a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0498b5abb552808825bda07555c8d98a02676cac))
* type core runtime startup task contracts ([5dad0d6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5dad0d6882795eca689e145734b84e92111d441d))
* type integration bootstrap startup stages ([30ef194](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/30ef1945dec2997c9a59a7b814ca6a8181fad386))
* type payment runtime bootstrap interfaces ([8f748bb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8f748bbf60e96249796801d0786aa3d503cfa563))
* type remaining bootstrap utility stages ([d10758a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d10758a313e46dbbc605cc59c04e773982110669))
* type runtime task startup stages ([7049e18](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7049e18c4bf9b86e768010b06b98c12d283950d9))
* type runtime watchdog loop interfaces ([ae2fdab](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ae2fdab62bd514de6847bf0332b5446a2f1adc2e))
* type startup summary and finalize stages ([68cd40c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/68cd40c8f166628b25edeffc39ede9778e2c4111))
* type telegram notifier in bootstrap pipeline ([f206570](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f2065708fc8fc8eae5a757bf302d71f45ed52c9a))
* unify alembic command executor path ([ba974f6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ba974f635afaefc0bce921e9765e215f682211e1))
* unify payment CRUD compatibility wrappers ([0d944e9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0d944e9222ca3a7311c608f54f17f162fa4b1e8e))
* unify runtime startup stage invocation ([5159106](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5159106d03c1eb05fc1b08c8df14a64b05a0c17d))
* unify runtime task shutdown handling ([8520d14](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8520d14a011d9ced7c8950480ce7389201d441df))
* unify web shutdown guarded calls ([a00ebbd](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a00ebbd4c8921065bf9f8a238276653dce4878fb))
* use running loop in broadcast timing paths ([9f7e6ee](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9f7e6ee0704297904e73622fe685a5e7159a64ec))

## [3.19.0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.18.0...v3.19.0) (2026-02-20)


### New Features

* **cabinet:** add admin menu-layout endpoints ([4e8a3ce](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4e8a3ce020d27b50d710e2581404538867bfda8a))


### Bug Fixes

* **menu:** enable custom buttons in cabinet mode ([3e08e6a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3e08e6ad65379a8190efcfb74b3772780f0f7160))
* skip blocked users in trial notifications and broadcasts without DB status change ([493f315](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/493f315a65610826a04e04c3d2065e0b395426ed))

## [3.18.0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.17.1...v3.18.0) (2026-02-18)


### New Features

* add campaign_id to ReferralEarning for campaign attribution ([0c07812](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0c07812ecc9502f54a7745a77b086fc52bdc0e34))
* enforce 1-to-1 partner-campaign binding with partner info in campaigns ([366df18](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/366df18c547047a7c69192c768970ebc6ee426fc))
* expose traffic_reset_mode in subscription response ([59383bd](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/59383bdbd8c72428d151cb24d132452414b14fa3))
* expose traffic_reset_mode in tariff API response ([5d4a94b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5d4a94b8cea8f16f0b4c31e24a4695bee4c67af7))


### Bug Fixes

* 3 user deletion bugs — type cast, inner savepoint, lazy load ([af31c55](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/af31c551d2f23ef01425bdb2db8f255dbc3047e2))
* add blocked_count column migration to universal_migration.py ([b4b10c9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b4b10c998cadbb879540e56dbd0e362b5497ee57))
* add migration for partner system tables and columns ([4645be5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4645be53cbb3799aa6b2b6a623af30460357a554))
* add migration for partner system tables and columns ([79ea398](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/79ea398d1db436a7812a799bf01b2c1c3b1b73be))
* add missing payment providers to payment_utils and fix {total_amount} formatting ([bdb6161](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/bdb61613de378efab4de6de98fde2de3b554c548))
* add selectinload for subscription in campaign user list ([eb9dba3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/eb9dba3f4728b478f2206ff992700a9677f879c7))
* **async:** offload blocking Path operations to threads ([9d298fa](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9d298fabad791e2d2ba48950f44e8e1f2e90cca5))
* auth middleware catches all commit errors, not just connection errors ([6409b0c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6409b0c023cd7957c43d5c1c3d83e671ccaf959c))
* auto-convert naive datetimes to UTC-aware on model load ([f7d33a7](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f7d33a7d2b31145a839ee54676816aa657ac90da))
* connected_squads stores UUIDs, not int IDs — use get_server_ids_by_uuids ([d7039d7](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d7039d75a47fbf67436a9d39f2cd9f65f2646544))
* correct subscription_service import in broadcast cleanup ([6c4e035](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6c4e035146934dffb576477cc75f7365b2f27b99))
* deadlock on user deletion + robust migration 0002 ([b7b83ab](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b7b83abb723913b3167e7462ff592a374c3f421b))
* eliminate deadlock by matching lock order with webhook ([d651a6c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d651a6c02f501b7a0ded570f2db6addcc16173a9))
* extend naive datetime guard to all model properties ([bd11801](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/bd11801467e917d76005d1a782c71f5ae4ffee6e))
* handle naive datetime in raw SQL row comparison (payment/common) ([38f3a9a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/38f3a9a16a24e85adf473f2150aad31574a87060))
* handle naive datetimes in Subscription properties ([e512e5f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e512e5fe6e9009992b5bc8b9be7f53e0612f234a))
* make migration 0002 robust with table existence checks ([f076269](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f076269c323726c683a38db092d907591a26e647))
* prevent fileConfig from destroying structlog handlers ([e78b104](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e78b1040a50ac14759bceab396d0c3e34dd79cdd))
* return zeroed stats dict when withdrawal is disabled ([7883efc](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7883efc3d6e6d8bedf8e4b7d72634cbab6e2f3d7))
* use AwareDateTime TypeDecorator for all datetime columns ([a7f3d65](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a7f3d652c51ecd653900a530b7d38feaf603ecf1))
* wrap user deletion steps in savepoints to prevent transaction cascade abort ([a38dfcb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a38dfcb75a47a185d979a8202f637d8b79812e67))


### Refactoring

* replace universal_migration.py with Alembic ([b6c7f91](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b6c7f91a7c79d108820c9f89c9070fde4843316c))
* replace universal_migration.py with Alembic ([784616b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/784616b349ef12b35ee021dd7a7b2a2ef9fc57f6))

## [3.17.1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.17.0...v3.17.1) (2026-02-18)


### Bug Fixes

* **account-linking:** humanize manual merge ticket messages in russian ([90ca1ab](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/90ca1ab380e643310833afe4877cc9daa9f461ce))
* **account-linking:** humanize manual merge ticket messages in russian ([eddc04b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/eddc04b05aa708e6b9b3bda9196d003a65f9a41d))

## [3.17.0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.16.1...v3.17.0) (2026-02-18)


### New Features

* **account-linking:** expose telegram relink cooldown metadata ([113148a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/113148a10675240423c2e0566dd649e1785cf2f2))
* **account-linking:** expose telegram relink cooldown metadata ([ec50d64](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ec50d6450a31971988882fd76b3de08537ca4a50))

## [3.16.1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.16.0...v3.16.1) (2026-02-17)


### Bug Fixes

* resolve ruff lint violations and align lint config ([c7b456e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c7b456efbba9498400fb0efeb401299787656fec))

## [3.16.0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/compare/v3.15.1...v3.16.0) (2026-02-17)


### New Features

* **account-linking:** add coded errors and manual merge ticket flow ([75798ae](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/75798aef470ac69bb1d9fa67f9dac44b60e23cae))
* **account-linking:** add secure link-code flow for auth providers ([2e7a601](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2e7a60142c76bf10ef3422becbf33cc7a4aab06c))
* **account-linking:** localize manual merge tickets and enforce telegram relink guard ([bfa2c31](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/bfa2c31aa9faa2f49c7e3f6a41d2c166d87ee5c2))
* add 'default' (no color) option for button styles ([10538e7](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/10538e735149bf3f3f2029ff44b94d11d48c478e))
* add admin device management endpoints ([c57de10](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c57de1081a9e905ba191f64c37221c36713c82a6))
* add admin traffic packages and device limit management ([2f90f91](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2f90f9134df58b8c0a329c20060efcf07d5d92f9))
* add admin traffic usage API ([aa1cd38](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/aa1cd3829c5c3671e220d49dd7ec2d83563e2cf9))
* add admin traffic usage API with per-node statistics ([6c2c25d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6c2c25d2ccb27446c822e4ed94d9351bfeaf4549))
* add admin updates endpoint for bot and cabinet releases ([11b8ab1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/11b8ab1959e83fafe405be0b76dfa3dd1580a68b))
* add all remaining RemnaWave webhook events (node, service, crm, device) ([1e37fd9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1e37fd9dd271814e644af591343cada6ab12d612))
* add button style and emoji support for cabinet mode (Bot API 9.4) ([bf2b2f1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/bf2b2f1c5650e527fcac0fb3e72b4e6e19bef406))
* add cabinet admin API for pinned messages management ([1a476c4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1a476c49c19d1ec2ab2cda1c2ffb5fd242288bb6))
* add close button to all webhook notifications ([d9de15a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d9de15a5a06aec3901415bdfd25b55d2ca01d28c))
* add endpoint for updating user referral commission percent ([da6f746](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/da6f746b093be8cdbf4e2889c50b35087fbc90de))
* add enrichment data to CSV export ([f2dbab6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f2dbab617155cdc41573d885f0e55222e5b9825b))
* add lite mode functionality with endpoints for retrieval and update ([7b0403a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7b0403a307702c24efefc5c14af8cb2fb7525671))
* add LOG_COLORS env setting to toggle console ANSI colors ([27309f5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/27309f53d9fa0ba9a2ca07a65feed96bf38f470c))
* add MULENPAY_WEBSITE_URL setting for post-payment redirect ([fe5f5de](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/fe5f5ded965e36300e1c73f25f16de22f84651ad))
* add node/status filters and custom date range to traffic page ([ad260d9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ad260d9fe0b232c9d65176502476212902909660))
* add node/status filters, custom date range, connected devices to traffic page ([9ea533a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9ea533a864e345647754f316bd27971fba1420af))
* add node/status filters, date range, devices to traffic page ([ad6522f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ad6522f547e68ef5965e70d395ca381b0a032093))
* add OAuth 2.0 authorization (Google, Yandex, Discord, VK) ([97be4af](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/97be4afbffd809fe2786a6d248fc4d3f770cb8cf))
* add panel info, node usage endpoints and campaign to user detail ([287a43b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/287a43ba6527ff3464a527821d746a68e5371bbe))
* add panel info, node usage endpoints and campaign to user detail ([0703212](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/070321230bcb868e4bc7a39c287ed3431a4aef4a))
* add per-button enable/disable toggle and custom labels per locale ([68773b7](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/68773b7e77aa344d18b0f304fa561c91d7631c05))
* add per-section button style and emoji customization via admin API ([a968791](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a9687912dfe756e7d772d96cc253f78f2e97185c))
* add Persian (fa) locale with complete translations ([29a3b39](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/29a3b395b6e67e4ce2437b75120b78c76b69ff4f))
* add RemnaWave incoming webhooks for real-time subscription events ([6d67cad](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6d67cad3e7aa07b8490d88b73c38c4aca6b9e315))
* add risk columns to traffic CSV export ([7c1a142](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7c1a1426537e43d14eff0a1c3faeca484611b58b))
* add server-side sorting for enrichment columns ([15c7cc2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/15c7cc2a58e1f1935d10712a981466629db251d1))
* add startup warnings for missing HAPP_CRYPTOLINK_REDIRECT_TEMPLATE and MINIAPP_CUSTOM_URL ([476b89f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/476b89fe8e613c505acfc58a9554d31ccf92718a))
* add system info endpoint for admin dashboard ([02c30f8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/02c30f8e7eb6ba90ed8983cfd82199a22b473bbf))
* add tariff filter, fix traffic data aggregation ([fa01819](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/fa01819674b2d2abb0d05b470559b09eb43abef8))
* add tariff reorder API endpoint ([4c2e11e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4c2e11e64bed41592f5a12061dcca74ce43e0806))
* add traffic usage enrichment endpoint with devices, spending, dates, last node ([5cf3f2f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5cf3f2f76eb2cd93282f845ea0850f6707bfcc09))
* add TRIAL_DISABLED_FOR setting to disable trial by user type ([c4794db](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c4794db1dd78f7c48b5da896bdb2f000e493e079))
* add user_id filter to admin tickets endpoint ([8886d0d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8886d0dea20aa5a31c6b6f0c3391b3c012b4b34d))
* add user_id filter to admin tickets endpoint ([d3819c4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d3819c492f88794e4466c2da986fd3a928d7f3df))
* add web admin button for admins in cabinet mode ([9ac6da4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9ac6da490dffa03ce823009c6b4e5014b7d2bdfb))
* add web campaign links with bonus processing in auth flow ([d955279](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d9552799c17a76e2cc2118699528c5b591bd97fb))
* admin panel enhancements & bug fixes ([e6ebf81](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e6ebf81752499df8eb0a710072785e3d603dba33))
* allow tariff deletion with active subscriptions ([ebd6bee](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ebd6bee05ed7d9187de9394c64dfd745bb06b65a))
* **auth:** add manual merge moderation and secure telegram-otp unlink flow ([ab281f4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ab281f40aa8e3dffdfb123c24f046ce10a71a8f3))
* block registration with disposable email addresses ([9ca24ef](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9ca24efe434278925c0c1f8d2f2d644a67985c89))
* block registration with disposable email addresses ([116c845](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/116c8453bb371b5eacf5c9d07f497eb449a355cc))
* **ci:** add release-please and release workflows ([488d5c9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/488d5c99f7bd6bd1927e2125a824d43376cf3403))
* **ci:** add release-please and release workflows ([9151882](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9151882245a325761d75eab3a58d0f677219c31b))
* colored console logs via structlog + rich + FORCE_COLOR ([bf64611](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/bf646112df02aa7aa7918d0513cb6968ceb7f378))
* disable trial by user type (email/telegram/all) ([4e7438b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4e7438b9f9c01e30c48fcf2bbe191e9b11598185))
* handle errors.bandwidth_usage_threshold_reached_max_notifications webhook ([8e85e24](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8e85e244cb786fb4c06162f2b98d01202e893315))
* handle service.subpage_config_changed webhook event ([43a326a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/43a326a98ccc3351de04d9b2d660d3e7e0cb0efc))
* **localization:** add Persian (fa) locale support and wire it across app flows ([cc54a7a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/cc54a7ad2fb98fe6e662e1923027f4989ae72868))
* migrate OAuth state storage from in-memory to Redis ([e9b98b8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e9b98b837a8552360ef4c41f6cd7a5779aa8b0a7))
* node/status filters + custom date range for traffic page ([a161e2f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a161e2f904732b459fef98a67abfaae1214ecfd4))
* **notifications:** redesign version update notification ([02eca28](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/02eca28bc0f9d31495d7bbe5deb380d13e859c3f))
* **notifications:** redesign version update notification ([3f7ca7b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3f7ca7be3ade6892e453f86ac0c62e61ac61a11c))
* OAuth 2.0 authorization (Google, Yandex, Discord, VK) ([3cbb9ef](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3cbb9ef024695352959ef9a82bf8b81f0ba1d940))
* pass platform-level fields from RemnaWave config to frontend ([095bc00](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/095bc00b33d7082558a8b7252906db2850dce9da))
* rename MAIN_MENU_MODE=text to cabinet with deep-linking to frontend sections ([ad87c5f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ad87c5fb5e1a4dd0ef7691f12764d3df1530f643))
* return 30-day daily breakdown for node usage ([7102c50](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7102c50f52d583add863331e96f3a9de189f581a))
* return 30-day daily breakdown for node usage ([e4c65ca](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e4c65ca220994cf08ed3510f51d9e2808bb2d154))
* serve original RemnaWave config from app-config endpoint ([43762ce](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/43762ce8f4fa7142a1ca62a92b97a027dab2564d))
* show all active webhook endpoints in startup log ([9d71005](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9d710050ad40ba76a14aa6ace8e8a47f25cdde94))
* tariff filter + fix traffic data aggregation ([1021c2c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1021c2cdcd07cf2194e59af7b59491108339e61f))
* tariff reorder API endpoint ([085a617](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/085a61721a8175b3f4fd744614c446d73346f2b7))
* traffic filters, date range & risk columns in CSV export ([4c40b5b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4c40b5b370616a9ab40cbf0cccdbc0ac4a3f8278))
* unified notification delivery for webhook events (email + WS support) ([26637f0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/26637f0ae5c7264c0430487d942744fd034e78e8))
* webhook protection — prevent sync/monitoring from overwriting webhook data ([184c52d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/184c52d4ea3ce02d40cf8a5ab42be855c7c7ae23))


### Bug Fixes

* **account-linking:** allow auto-merge when source has trial only ([c3713f7](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c3713f7e628e57559890dde10de86368bc560505))
* **account-linking:** allow merge with trial remna and transfer balance ([5cc3ec6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5cc3ec6a7a0febe0cba9a6d00fe939ef22ba6381))
* **account-linking:** allow unlink of current auth provider when other identities exist ([afdc2f2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/afdc2f2956874c23ce5a092266c21282594d28ae))
* **account-linking:** apply telegram relink cooldown to resulting primary account ([9facc81](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9facc810528a5fdb3995bb0cce7404ecf15f585d))
* **account-linking:** auto-select primary account by data presence ([5815a7d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5815a7d0ef44a9f2d6533b1ff3c0fcc4b1e8daf7))
* **account-linking:** handle external identity unique conflicts ([a43c9a9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a43c9a94ec0de3113f407986242ed1fb9d7c4c8c))
* **account-linking:** make manual merge resolution messages human-readable ([615d7c4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/615d7c411675543bccfc4a30275f722e1a14092b))
* add /start burst rate-limit to prevent spam abuse ([61a9722](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/61a97220d30031816ab23e33a46717e4895c0758))
* add action buttons to webhook notifications and fix empty device names ([7091eb9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7091eb9c148aaf913c4699fc86fef5b548002668))
* add debug logging for bulk device response structure ([46da31d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/46da31d89c55c225dec9136d225f2db967cf8961))
* add email field to traffic table for OAuth/email users ([94fcf20](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/94fcf20d17c54efd67fa7bd47eff1afdd1507e08))
* add email/UUID fallback for OAuth user panel sync ([165965d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/165965d8ea60a002c061fd75f88b759f2da66d7d))
* add enrichment device mapping debug logs ([5be82f2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5be82f2d78aed9b54d74e86f261baa5655e5dcd9))
* add missing placeholders to Arabic SUBSCRIPTION_INFO template ([fe54640](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/fe546408857128649930de9473c7cde1f7cc450a))
* add naive datetime guards to fromisoformat() in Redis cache readers ([1b3e6f2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1b3e6f2f11c20aa240da1beb11dd7dfb20dbe6e8))
* add naive datetime guards to fromisoformat() in Redis cache readers ([6fa4948](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6fa49485d9f1cd678cb5f9fa7d0375fd47643239))
* add naive datetime guards to parsers and fix test datetime literals ([0946090](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/094609005af7358bf5d34d252fc66685bd25751c))
* add passive_deletes to Subscription relationships to prevent NOT NULL violation on cascade delete ([bfd66c4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/bfd66c42c1fba3763f41d641cea1bd101ec8c10c))
* add promo code anti-abuse protections ([97ec39a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/97ec39aa803f0e3f03fdcd482df0cbcb86fd1efd))
* add refresh before assigning promo_groups to avoid async lazy lo… ([733be09](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/733be0965806607cef8beb30685052af22a13ab4))
* add refresh before assigning promo_groups to avoid async lazy load error ([5e75210](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5e75210c8b3da1a738c94edf3dd02a18bbff3bb6))
* add startup warning for missing HAPP_CRYPTOLINK_REDIRECT_TEMPLATE in guide mode ([1d43ae5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1d43ae5e25ffcf0e4fe6fec13319d393717e1e50))
* address remaining abs() issues from review ([ff21b27](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ff21b27b98bb5a7517e06057eb319c9f3ebb74c7))
* address review issues in backup, updates, and webhook handlers ([2094886](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/20948869902dc570681b05709ac8d51996330a6e))
* allow email change for unverified emails ([93bb8e0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/93bb8e0eb492ca59e29da86594e84e9c486fea65))
* allow non-HTTP deep links in crypto link webhook updates ([f779225](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f77922522a85b3017be44b5fc71da9c95ec16379))
* allow purchase when recalculated price is lower than cached ([19dabf3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/19dabf38512ae0c2121108d0b92fc8f384292484))
* AttributeError in withdrawal admin notification (send_to_admins → send_admin_notification) ([c75ec0b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c75ec0b22a3f674d3e1a24b9d546eca1998701b3))
* **auth:** add unlink otp anti-spam limits ([5a14d7a](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5a14d7a901ff9e4afb0c6082e6725eb0d7a6a78e))
* **autopay:** add 6h cooldown for insufficient balance notifications ([f7abe03](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f7abe03dba085b07fc1dc0fc0f21613e6a6219eb))
* **autopay:** add 6h cooldown for insufficient balance notifications ([992a5cb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/992a5cb97f5517b52bd386907a2cbc2162182c44))
* **autopay:** exclude daily subscriptions from global autopay ([3d94e63](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3d94e63c3ca4688d5f0b513e6b678afdd3798eea))
* **autopay:** exclude daily subscriptions from global autopay ([b9352a5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b9352a5bd53ec82114abd46156bacc0e496dcfe1))
* **broadcast:** resolve SQLAlchemy connection closed errors ([94a00ab](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/94a00ab2694d2b13c93c73a4defb2c2019225093))
* **broadcast:** resolve SQLAlchemy connection closed errors during long broadcasts ([b8682ad](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b8682adbbfa1674f03ea8699de4b3bd125092a9b))
* **broadcast:** stabilize mass broadcast for 100k+ users ([7956951](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/79569510d29494c0be46a8f39bc4a01e30873f21))
* **broadcast:** stabilize mass broadcast for 100k+ users ([13ebfdb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/13ebfdb5c45f2d358b2552bfcc2e3b907ec7d567))
* build composite device name from platform + hwid short suffix ([17ce640](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/17ce64037f198837c8f2aa7bf863871f60bdf547))
* **cabinet:** apply promo group discounts to addons and tariff switch ([e8a413c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e8a413c3c3177d8ce4931d2f82c17dce70e9aaad))
* **cabinet:** apply promo group discounts to device/traffic purchase and tariff switch ([aa1d328](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/aa1d3289e1bb2195a11c333867ac131c5460f0cc))
* change CryptoBot URL priority to bot_invoice_url for Telegram opening ([3193ffb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3193ffbd1bee07cb79824d87cb0f77b473b22989))
* clean stale squad UUIDs from tariffs during server sync ([fcaa9df](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/fcaa9dfb27350ceda3765c6980ad67f671477caf))
* clear subscription data when user deleted from Remnawave panel ([b0fd38d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b0fd38d60c22247a0086c570665b92c73a060f2f))
* close unclosed HTML tags in version notification ([0b61c7f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0b61c7fe482e7bbfbb3421307a96d54addfd91ee))
* close unclosed HTML tags when truncating version notification ([b674550](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b6745508da861af9b2ff05d89b4ac9a3933da510))
* complete datetime.utcnow() → datetime.now(UTC) migration ([eb18994](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/eb18994b7d34d777ca39d3278d509e41359e2a85))
* correct response parsing for non-legacy node-users endpoint ([a076dfb](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a076dfb5503a349450b5aa8aac3c6f40070b715d))
* correct response parsing for non-legacy node-users endpoint ([91ac90c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/91ac90c2aecfb990679b3d0c835314dde448886a))
* daily tariff subscriptions stuck in expired/disabled with no resume path ([80914c1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/80914c1af739aa0ee1ea75b0e5871bf391b9020d))
* delete subscription_servers before subscription to prevent FK violation ([7d9ced8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7d9ced8f4f71b43ed4ac798e6ff904a086e1ac4a))
* don't delete Heleket invoice message on status check ([9943253](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/994325360ca7665800177bfad8f831154f4d733f))
* downgrade Telegram timeout errors to warning in monitoring service ([e43a8d6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e43a8d6ce4c40a7212bf90644f82da109717bdcb))
* downgrade transient API errors (502/503/504) to warning level ([ec8eaf5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ec8eaf52bfdc2bde612e4fc0324575ba7dc6b2e1))
* enforce blacklist via middleware ([561708b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/561708b7772ec5b84d6ee049aeba26dc70675583))
* enforce blacklist via middleware instead of per-handler checks ([966a599](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/966a599c2c778dce9eea3c61adf6067fb33119f6))
* exclude signature field from Telegram initData HMAC validation ([5b64046](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5b6404613772610c595e55bde1249cdf6ec3269d))
* expand backup coverage to all 68 models and harden restore ([02e40bd](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/02e40bd6f7ef8e653cae53ccd127f2f79009e0d4))
* extract device name from nested hwidUserDevice object ([79793c4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/79793c47bbbdae8b0f285448d5f70e90c9d4f4b0))
* filter out traffic packages with zero price from purchase options ([64a684c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/64a684cd2ff51e663a1f70e61c07ca6b4f6bfc91))
* flood control handling in pinned messages and XSS hardening in HTML sanitizer ([454b831](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/454b83138e4db8dc4f07171ee6fe262d2cd6d311))
* force basicConfig to replace pre-existing handlers ([7eb8d4e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/7eb8d4e153bab640a5829f75bfa6f70df5763284))
* handle FK violation in create_yookassa_payment when user is deleted ([55d281b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/55d281b0e37a6e8977ceff792cccb8669560945b))
* handle mixed types in traffic sort ([eeed2d6](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/eeed2d6369b07860505c59bcff391e7b17e0ffb7))
* handle mixed types in traffic sort for string fields ([a194be0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a194be0843856b3376167d9ba8a8ef737280998c))
* handle nullable traffic_limit_gb and end_date in subscription model ([e94b93d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e94b93d0c10b4e61d7750ca47e1b2f888f5873ed))
* handle photo message in ticket creation flow ([e182280](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e1822800aba3ea5eee721846b1e0d8df0a9398d1))
* handle StaleDataError in webhook user.deleted server counter decrement ([c30c2fe](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c30c2feee1db03f0a359b291117da88002dd0fe0))
* handle StaleDataError in webhook when user already deleted ([d58a80f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d58a80f3eaa64a6fc899e10b3b14584fb7fc18a9))
* handle tariff_extend callback without period (back button crash) ([ba0a5e9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ba0a5e9abd9bd582968d69a5c6e57f336094c782))
* handle TelegramBadRequest in ticket edit_message_text calls ([8e61fe4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8e61fe47746da2ac09c3ea8c4dbfc6be198e49e3))
* handle time/date types in backup JSON serialization ([27365b3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/27365b3c7518c09229afcd928f505d0f3f66213f))
* handle unique constraint conflicts during backup restore without clear_existing ([5893874](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/589387477624691e0026086800428e7e52e06128))
* harden backup create/restore against serialization and constraint errors ([fc42916](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/fc42916b10bb698895eb75c0e2568747647555d3))
* HTML parse fallback, email change race condition, username length limit ([d05ff67](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d05ff678abfacaa7e55ad3e55f226d706d32a7b7))
* ignore 'message is not modified' on privacy policy decline ([be1da97](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/be1da976e14a35e6cca01a7fca7529c55c1a208b))
* improve button URL resolution and pass uiConfig to frontend ([0ed98c3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0ed98c39b6c95911a38a26a32d0ffbcf9cfd7c80))
* include additional devices in tariff renewal price and display ([17e9259](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/17e9259eb1d41dbf1d313b6a7d500f6458359393))
* increase OAuth HTTP timeout to 30s ([333a3c5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/333a3c590120a64f6b2963efab1edd861274840c))
* limit Rich traceback output to prevent console flood ([11ef714](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/11ef714e0dde25a08711c0daeee943b6e71e20b7))
* move /settings routes before /{ticket_id} to fix route matching ([000d670](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/000d670869bc7eb0eb6551e1d9eabbe05cd34ea2))
* move /settings routes before /{ticket_id} to fix route matching ([0c9b69d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0c9b69deb0686c8e078eaf627693b84b03ffdd3c))
* NameError in set_user_devices_button — undefined action_text ([1b8ef69](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1b8ef69a1bbb7d8d86827cf7aaa4f05cbf480d75))
* normalize transaction amount signs across all aggregations ([4247981](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4247981c98111af388c98628c1e61f0517c57417))
* nullify payment FK references before deleting transactions in user restoration ([0b86f37](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0b86f379b4e55e499ca3d189137e2aed865774b5))
* **oauth:** add yandex retry and fallback endpoints ([4633351](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/46333517c8ba69de67b1e0be2e73517e50a3e94c))
* **oauth:** backfill missing profile fields on login ([1e545d7](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1e545d71394fc3f25b4f3b0b92c06f112f48195c))
* **oauth:** fill vk profile fallbacks for empty userinfo ([410870c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/410870cb9798983e8b5801bf4147973390fb4baa))
* **oauth:** migrate vk login to vk id pkce flow ([15a22bf](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/15a22bfb1a3a4ba6573a4865086e4b54064ed5e8))
* **oauth:** use yandex.ru authorize endpoint ([ea2fdda](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ea2fddaadbf0ad01b5ebe6821651a74be6960518))
* paginate bulk device endpoint to fetch all HWID devices ([4648a82](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/4648a82da959410603c92055bcde7f96131e0c29))
* parse bandwidth stats series format for node usage ([557dbf3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/557dbf3ebe777d2137e0e28303dc2a803b15c1c6))
* parse bandwidth stats series format for node usage ([462f7a9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/462f7a99b9d5c0b7436dbc3d6ab5db6c6cfa3118))
* pass tariff object instead of tariff_id to set_tariff_promo_groups ([1ffb8a5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1ffb8a5b85455396006e1fcddd48f4c9a2ca2700))
* payment race conditions, balance atomicity, renewal rollback safety ([c5124b9](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c5124b97b63eda59b52d2cbf9e2dcdaa6141ed6e))
* pre-validate CABINET_BUTTON_STYLE to prevent invalid values from suppressing per-section defaults ([46c1a69](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/46c1a69456036cb1be784b8d952f27110e9124eb))
* preserve payment initiation time in transaction created_at ([90d9df8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/90d9df8f0e949913f09c4ebed8fe5280453ab3ab))
* preserve purchased traffic when extending same tariff ([b167ed3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b167ed3dd1c6e6239db2bdbb8424bcb1fb7715d9))
* prevent cascading greenlet errors after sync rollback ([a1ffd5b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a1ffd5bda6b63145104ce750835d8e6492d781dc))
* prevent negative amounts in spent display and balance history ([c30972f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c30972f6a7911a89a6c3f2080019ff465d11b597))
* prevent sync from overwriting end_date for non-ACTIVE panel users ([49871f8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/49871f82f37d84979ea9ec91055e3f046d5854be))
* promo code max_uses=0 conversion and trial UX after promo activation ([1cae713](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1cae7130bc87493ab8c7691b3c22ead8189dab55))
* protect server counter callers and fix tariff change detection ([bee4aa4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/bee4aa42842b8b6611c7c268bcfced408a227bc0))
* query per-node legacy endpoint for user traffic breakdown ([b94e3ed](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b94e3edf80e747077992c03882119c7559ad1c31))
* query per-node legacy endpoint for user traffic breakdown ([51ca3e4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/51ca3e42b75c1870c76a1b25f667629855cfe886))
* read bot version from pyproject.toml when VERSION env is not set ([9828ff0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9828ff0845ec1d199a6fa63fe490ad3570cf9c8f))
* reduce node usage to 2 API calls to avoid 429 rate limit ([c68c4e5](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c68c4e59846abba9c7c78ae91ec18e2e0e329e3c))
* reduce node usage to 2 API calls to avoid 429 rate limit ([f00a051](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f00a051bb323e5ba94a3c38939870986726ed58e))
* release-please config — remove blocked workflow files ([d88ca98](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d88ca980ec67e303e37f0094a2912471929b4cef))
* remove DisplayNameRestrictionMiddleware ([640da34](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/640da3473662cfdcceaa4346729467600ac3b14f))
* remove dots from Remnawave username sanitization ([d6fa86b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d6fa86b870eccbf22327cd205539dd2084f0014e))
* remove local UTC re-imports shadowing module-level import in purchase.py ([e68760c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e68760cc668016209f4f19a2e08af8680343d6ed))
* remove redundant trial inactivity monitoring checks ([d712ab8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d712ab830166cab61ce38dd32498a8a9e3e602b0))
* remove unused PaymentService from MonitoringService init ([491a7e1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/491a7e1c425a355e55b3020e2bcc7b96047bdf5e))
* remove workflow files and pyproject.toml from release-please extra-files ([5070bb3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5070bb34e8a09b2641783f5e818bb624469ad610))
* replace deprecated Query(regex=) with pattern= ([871ceb8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/871ceb866ccf1f3a770c7ef33406e1a43d0a7ff7))
* resolve 429 rate limiting on traffic page ([b12544d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b12544d3ea8f4bbd2d8c941f83ee3ac412157adb))
* resolve 429 rate limiting on traffic page ([924d6bc](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/924d6bc09c815c1d188ea1d0e7974f7e803c1d3f))
* resolve deadlock on server_squads counter updates and add webhook notification toggles ([57dc1ff](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/57dc1ff47f2f6183351db7594544a07ca6f27250))
* resolve exc_info for admin notifications, clean log formatting ([11f8af0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/11f8af003fc60384abafa2b670b89d6ad3ac57a4))
* resolve HWID reset and webhook FK violation ([5f3e426](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5f3e426750c2adcb097b92f1a9e7725b1c5c5eba))
* resolve HWID reset context manager bug and webhook FK violation ([a9eee19](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a9eee19c95efdc38ecf5fa28f7402a2bbba7dd07))
* resolve merge conflict in release-please config ([0ef4f55](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0ef4f55304751571754f2027105af3e507f75dfd))
* resolve MissingGreenlet error when accessing subscription.tariff ([a93a32f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a93a32f3a7d1b259a2e24954ae5d2b7c966c5639))
* resolve multiple production errors and performance issues ([071c23d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/071c23dd5297c20527442cb5d348d498ebf20af4))
* restore unquote for user data parsing in telegram auth ([c2cabbe](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c2cabbee097a41a95d16c34d43ab7e70d076c4dc))
* revert device pagination, add raw user data field discovery ([8f7fa76](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8f7fa76e6ab34a3ad2f61f4e1f06026fd3fbf4e3))
* safe HTML preview truncation and lazy-load subscription fallback ([40d8a6d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/40d8a6dc8baf3f0f7c30b0883898b4655a907eb5))
* security and architecture fixes for webhook handlers ([dc1e96b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/dc1e96bbe9b4496e91e9dea591c7fc0ef4cc245b))
* skip users with active subscriptions in admin inactive cleanup ([e79f598](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/e79f598d17ffa76372e6f88d2a498accf8175c76))
* stop CryptoBot webhook retry loop and save cabinet payments to DB ([2cb6d73](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2cb6d731e96cbfc305b098d8424b84bfd6826fb4))
* suppress 'message is not modified' error in updates panel ([3a680b4](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/3a680b41b0124848572809d187cab720e1db8506))
* suppress bot-blocked-by-user error in AuthMiddleware ([fda9f3b](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/fda9f3beecbfcca4d7abc16cf661d5ad5e3b5141))
* suppress expired callback query error in AuthMiddleware ([2de4384](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/2de438426a647e2bcae9b4d99eef4093ff8b5429))
* suppress startup log noise (~350 lines → ~30) ([8a6650e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/8a6650e57cd8ea396d9b057a7753469947f38d29))
* sync subscription status from panel in user.modified webhook ([5156d63](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5156d635f0b5bc0493e8f18ce9710cca6ff4ffc8))
* sync support mode from cabinet admin to SupportSettingsService ([516be6e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/516be6e600a08ad700d83b793dc64b2ca07bdf44))
* sync SUPPORT_SYSTEM_MODE between SystemSettings and SupportSettings ([0807a9f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0807a9ff19d1eb4f1204f7cbeb1da1c1cfefe83a))
* ticket creation crash and webhook PendingRollbackError ([760c833](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/760c833b7402541d3c7cf2ed7fc0418119e75042))
* traceback in Telegram notifications + reduce log padding ([909a403](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/909a4039c43b910761bd05c36e79c8e6773199db))
* UnboundLocalError for get_logo_media in required_sub_channel_check ([d3c14ac](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d3c14ac30363839d1340129f279a7a7b4b021ed1))
* use accessible nodes API and fix date format for node usage ([943e9a8](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/943e9a86aaa449cd3154b0919cfdc52d2a35b509))
* use accessible nodes API and fix date format for node usage ([c4da591](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/c4da59173155e2eeb69eca21416f816fcbd1fa9c))
* use actual DB columns for subscription fallback query ([f0e7f8e](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f0e7f8e3bec27d97a3f22445948b8dde37a92438))
* use bulk device endpoint instead of per-user calls ([5f219c3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/5f219c33e6d49b0e3e4405a57f8344a4237f1002))
* use callback fallback when MINIAPP_CUSTOM_URL is not set ([eaf3a07](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/eaf3a07579729031030308d77f61a5227b796c02))
* use correct pagination params (start/size) for bulk HWID devices ([17af51c](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/17af51ce0bdfa45197384988d56960a1918ab709))
* use event field directly as event_name (already includes scope prefix) ([9aa22af](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9aa22af3390a249d1b500d75a7d7189daaed265e))
* use flush instead of commit in server counter functions ([6cec024](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/6cec024e46ef9177cb59aa81590953c9a75d81bb))
* use legacy per-node endpoint for traffic aggregation ([cc1c8ba](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/cc1c8bacb42a9089021b7ae0fecd1f2717953efb))
* use legacy per-node endpoint with correct response format ([b707b79](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b707b7995b90c6465910a35e9a4403e1408c6568))
* use PaymentService for cabinet YooKassa payments ([61bb8fc](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/61bb8fcafd94509568f134ccdba7769b66cc7d5d))
* use PaymentService for cabinet YooKassa payments to save local DB record ([ff5bba3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ff5bba3fc5d1e1b08d008b64215e487a9eb70960))
* use per-user panel endpoints for reliable device counts and last node data ([9d39901](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/9d39901f78ece55c740a5df2603601e5d0b1caca))
* use selection.period.days instead of selection.period_days ([4541016](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/45410168afe683675003a1c41c17074a54ce04f1))
* use sync context manager for structlog bound_contextvars ([25e8c9f](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/25e8c9f8fc4d2c66d5a1407d3de5c7402dc596da))
* use traffic topup config and add WATA 429 retry ([b5998ea](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/b5998ea9d22644ed2914b0e829b3a76a32a69ddf))
* webhook notification 'My Subscription' button uses unregistered callback_data ([1e2a7e3](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1e2a7e3096af11540184d60885b8c08d73506c4a))
* webhook:close button not working due to channel check timeout ([019fbc1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/019fbc12b6cf61d374bbed4bce3823afc60445c9))


### Performance

* cache logo file_id to avoid re-uploading on every message ([142ff14](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/142ff14a502e629446be7d67fab880d12bee149d))


### Refactoring

* add strict typing to OAuth providers, replace urlencode with httpx params ([0de6418](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/0de6418bca39fb1b72c49d7c89d1a169722ec9e8))
* complete structlog migration with contextvars, kwargs, and logging hardening ([1f0fef1](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/1f0fef114bd979b2b0d2bd38dde6ce05e7bba07b))
* fix transaction boundaries, extract _finalize_oauth_login, replace deprecated datetime.utcnow ([41633af](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/41633af7631cce084f9ff6e7ceb27b27ed340d95))
* improve log formatting — logger name prefix and table alignment ([f637204](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/f63720467a935bdaaa58bb34d588d65e46698f26))
* remove "both" mode from BOT_RUN_MODE, keep only polling and webhook ([efa3a5d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/efa3a5d4579f24dabeeba01a4f2e981144dd6022))
* remove duplicated helpers, import from auth.py ([ccd9ab0](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ccd9ab02c5b7add1440efc6f1aafc93bb668e57a))
* remove Flask, use FastAPI exclusively for all webhooks ([119f463](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/119f463c36a95685c3bc6cdf704e746b0ba20d56))
* remove modem functionality from classic subscriptions ([ee2e79d](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/ee2e79db3114fe7a9852d2cd33c4b4fbbde311ea))
* remove smart auto-activation & activation prompt, fix production bugs ([a3903a2](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/a3903a252efdd0db4b42ca3fd6771f1627050a7f))
* replace dataclass with BaseModel for OAuthUserInfo ([d0a9cfe](https://github.com/PEDZEO/remnawave-bedolaga-telegram-bot/commit/d0a9cfe6a9611749ee215377ce632da64d393216))

## [3.15.1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.15.0...v3.15.1) (2026-02-17)


### Bug Fixes

* add naive datetime guards to fromisoformat() in Redis cache readers ([1b3e6f2](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/1b3e6f2f11c20aa240da1beb11dd7dfb20dbe6e8))
* add naive datetime guards to fromisoformat() in Redis cache readers ([6fa4948](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/6fa49485d9f1cd678cb5f9fa7d0375fd47643239))

## [3.15.0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.14.1...v3.15.0) (2026-02-17)


### New Features

* add LOG_COLORS env setting to toggle console ANSI colors ([27309f5](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/27309f53d9fa0ba9a2ca07a65feed96bf38f470c))
* add web campaign links with bonus processing in auth flow ([d955279](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/d9552799c17a76e2cc2118699528c5b591bd97fb))


### Bug Fixes

* AttributeError in withdrawal admin notification (send_to_admins → send_admin_notification) ([c75ec0b](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/c75ec0b22a3f674d3e1a24b9d546eca1998701b3))
* remove local UTC re-imports shadowing module-level import in purchase.py ([e68760c](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/e68760cc668016209f4f19a2e08af8680343d6ed))

## [3.14.1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.14.0...v3.14.1) (2026-02-17)


### Bug Fixes

* add naive datetime guards to parsers and fix test datetime literals ([0946090](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/094609005af7358bf5d34d252fc66685bd25751c))
* address remaining abs() issues from review ([ff21b27](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/ff21b27b98bb5a7517e06057eb319c9f3ebb74c7))
* complete datetime.utcnow() → datetime.now(UTC) migration ([eb18994](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/eb18994b7d34d777ca39d3278d509e41359e2a85))
* normalize transaction amount signs across all aggregations ([4247981](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/4247981c98111af388c98628c1e61f0517c57417))
* prevent negative amounts in spent display and balance history ([c30972f](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/c30972f6a7911a89a6c3f2080019ff465d11b597))

## [3.14.0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.13.0...v3.14.0) (2026-02-16)


### New Features

* show all active webhook endpoints in startup log ([9d71005](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/9d710050ad40ba76a14aa6ace8e8a47f25cdde94))


### Bug Fixes

* force basicConfig to replace pre-existing handlers ([7eb8d4e](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/7eb8d4e153bab640a5829f75bfa6f70df5763284))
* NameError in set_user_devices_button — undefined action_text ([1b8ef69](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/1b8ef69a1bbb7d8d86827cf7aaa4f05cbf480d75))
* remove unused PaymentService from MonitoringService init ([491a7e1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/491a7e1c425a355e55b3020e2bcc7b96047bdf5e))
* resolve MissingGreenlet error when accessing subscription.tariff ([a93a32f](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/a93a32f3a7d1b259a2e24954ae5d2b7c966c5639))
* sync support mode from cabinet admin to SupportSettingsService ([516be6e](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/516be6e600a08ad700d83b793dc64b2ca07bdf44))
* sync SUPPORT_SYSTEM_MODE between SystemSettings and SupportSettings ([0807a9f](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/0807a9ff19d1eb4f1204f7cbeb1da1c1cfefe83a))


### Refactoring

* improve log formatting — logger name prefix and table alignment ([f637204](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/f63720467a935bdaaa58bb34d588d65e46698f26))

## [3.13.0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.12.1...v3.13.0) (2026-02-16)


### New Features

* colored console logs via structlog + rich + FORCE_COLOR ([bf64611](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/bf646112df02aa7aa7918d0513cb6968ceb7f378))


### Bug Fixes

* limit Rich traceback output to prevent console flood ([11ef714](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/11ef714e0dde25a08711c0daeee943b6e71e20b7))
* resolve exc_info for admin notifications, clean log formatting ([11f8af0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/11f8af003fc60384abafa2b670b89d6ad3ac57a4))
* suppress startup log noise (~350 lines → ~30) ([8a6650e](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/8a6650e57cd8ea396d9b057a7753469947f38d29))
* traceback in Telegram notifications + reduce log padding ([909a403](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/909a4039c43b910761bd05c36e79c8e6773199db))
* use sync context manager for structlog bound_contextvars ([25e8c9f](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/25e8c9f8fc4d2c66d5a1407d3de5c7402dc596da))


### Refactoring

* complete structlog migration with contextvars, kwargs, and logging hardening ([1f0fef1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/1f0fef114bd979b2b0d2bd38dde6ce05e7bba07b))

## [3.12.1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.12.0...v3.12.1) (2026-02-16)


### Bug Fixes

* add /start burst rate-limit to prevent spam abuse ([61a9722](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/61a97220d30031816ab23e33a46717e4895c0758))
* add promo code anti-abuse protections ([97ec39a](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/97ec39aa803f0e3f03fdcd482df0cbcb86fd1efd))
* handle TelegramBadRequest in ticket edit_message_text calls ([8e61fe4](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/8e61fe47746da2ac09c3ea8c4dbfc6be198e49e3))
* replace deprecated Query(regex=) with pattern= ([871ceb8](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/871ceb866ccf1f3a770c7ef33406e1a43d0a7ff7))

## [3.12.0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.11.0...v3.12.0) (2026-02-15)


### New Features

* add 'default' (no color) option for button styles ([10538e7](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/10538e735149bf3f3f2029ff44b94d11d48c478e))
* add button style and emoji support for cabinet mode (Bot API 9.4) ([bf2b2f1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/bf2b2f1c5650e527fcac0fb3e72b4e6e19bef406))
* add per-button enable/disable toggle and custom labels per locale ([68773b7](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/68773b7e77aa344d18b0f304fa561c91d7631c05))
* add per-section button style and emoji customization via admin API ([a968791](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/a9687912dfe756e7d772d96cc253f78f2e97185c))
* add web admin button for admins in cabinet mode ([9ac6da4](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/9ac6da490dffa03ce823009c6b4e5014b7d2bdfb))
* rename MAIN_MENU_MODE=text to cabinet with deep-linking to frontend sections ([ad87c5f](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/ad87c5fb5e1a4dd0ef7691f12764d3df1530f643))


### Bug Fixes

* daily tariff subscriptions stuck in expired/disabled with no resume path ([80914c1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/80914c1af739aa0ee1ea75b0e5871bf391b9020d))
* filter out traffic packages with zero price from purchase options ([64a684c](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/64a684cd2ff51e663a1f70e61c07ca6b4f6bfc91))
* handle photo message in ticket creation flow ([e182280](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/e1822800aba3ea5eee721846b1e0d8df0a9398d1))
* handle tariff_extend callback without period (back button crash) ([ba0a5e9](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/ba0a5e9abd9bd582968d69a5c6e57f336094c782))
* pre-validate CABINET_BUTTON_STYLE to prevent invalid values from suppressing per-section defaults ([46c1a69](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/46c1a69456036cb1be784b8d952f27110e9124eb))
* remove redundant trial inactivity monitoring checks ([d712ab8](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/d712ab830166cab61ce38dd32498a8a9e3e602b0))
* webhook notification 'My Subscription' button uses unregistered callback_data ([1e2a7e3](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/1e2a7e3096af11540184d60885b8c08d73506c4a))

## [3.11.0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.10.3...v3.11.0) (2026-02-12)


### New Features

* add cabinet admin API for pinned messages management ([1a476c4](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/1a476c49c19d1ec2ab2cda1c2ffb5fd242288bb6))
* add startup warnings for missing HAPP_CRYPTOLINK_REDIRECT_TEMPLATE and MINIAPP_CUSTOM_URL ([476b89f](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/476b89fe8e613c505acfc58a9554d31ccf92718a))


### Bug Fixes

* add passive_deletes to Subscription relationships to prevent NOT NULL violation on cascade delete ([bfd66c4](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/bfd66c42c1fba3763f41d641cea1bd101ec8c10c))
* add startup warning for missing HAPP_CRYPTOLINK_REDIRECT_TEMPLATE in guide mode ([1d43ae5](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/1d43ae5e25ffcf0e4fe6fec13319d393717e1e50))
* flood control handling in pinned messages and XSS hardening in HTML sanitizer ([454b831](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/454b83138e4db8dc4f07171ee6fe262d2cd6d311))
* suppress expired callback query error in AuthMiddleware ([2de4384](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/2de438426a647e2bcae9b4d99eef4093ff8b5429))
* ticket creation crash and webhook PendingRollbackError ([760c833](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/760c833b7402541d3c7cf2ed7fc0418119e75042))

## [3.10.3](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.10.2...v3.10.3) (2026-02-12)


### Bug Fixes

* handle unique constraint conflicts during backup restore without clear_existing ([5893874](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/589387477624691e0026086800428e7e52e06128))
* harden backup create/restore against serialization and constraint errors ([fc42916](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/fc42916b10bb698895eb75c0e2568747647555d3))
* resolve deadlock on server_squads counter updates and add webhook notification toggles ([57dc1ff](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/57dc1ff47f2f6183351db7594544a07ca6f27250))

## [3.10.2](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.10.1...v3.10.2) (2026-02-12)


### Bug Fixes

* allow email change for unverified emails ([93bb8e0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/93bb8e0eb492ca59e29da86594e84e9c486fea65))
* clean stale squad UUIDs from tariffs during server sync ([fcaa9df](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/fcaa9dfb27350ceda3765c6980ad67f671477caf))
* delete subscription_servers before subscription to prevent FK violation ([7d9ced8](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/7d9ced8f4f71b43ed4ac798e6ff904a086e1ac4a))
* handle StaleDataError in webhook user.deleted server counter decrement ([c30c2fe](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/c30c2feee1db03f0a359b291117da88002dd0fe0))
* handle time/date types in backup JSON serialization ([27365b3](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/27365b3c7518c09229afcd928f505d0f3f66213f))
* HTML parse fallback, email change race condition, username length limit ([d05ff67](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/d05ff678abfacaa7e55ad3e55f226d706d32a7b7))
* payment race conditions, balance atomicity, renewal rollback safety ([c5124b9](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/c5124b97b63eda59b52d2cbf9e2dcdaa6141ed6e))
* remove DisplayNameRestrictionMiddleware ([640da34](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/640da3473662cfdcceaa4346729467600ac3b14f))
* suppress bot-blocked-by-user error in AuthMiddleware ([fda9f3b](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/fda9f3beecbfcca4d7abc16cf661d5ad5e3b5141))
* UnboundLocalError for get_logo_media in required_sub_channel_check ([d3c14ac](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/d3c14ac30363839d1340129f279a7a7b4b021ed1))
* use traffic topup config and add WATA 429 retry ([b5998ea](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/b5998ea9d22644ed2914b0e829b3a76a32a69ddf))


### Refactoring

* remove modem functionality from classic subscriptions ([ee2e79d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/ee2e79db3114fe7a9852d2cd33c4b4fbbde311ea))

## [3.10.1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.10.0...v3.10.1) (2026-02-11)


### Bug Fixes

* address review issues in backup, updates, and webhook handlers ([2094886](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/20948869902dc570681b05709ac8d51996330a6e))
* allow purchase when recalculated price is lower than cached ([19dabf3](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/19dabf38512ae0c2121108d0b92fc8f384292484))
* change CryptoBot URL priority to bot_invoice_url for Telegram opening ([3193ffb](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/3193ffbd1bee07cb79824d87cb0f77b473b22989))
* clear subscription data when user deleted from Remnawave panel ([b0fd38d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/b0fd38d60c22247a0086c570665b92c73a060f2f))
* downgrade Telegram timeout errors to warning in monitoring service ([e43a8d6](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/e43a8d6ce4c40a7212bf90644f82da109717bdcb))
* expand backup coverage to all 68 models and harden restore ([02e40bd](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/02e40bd6f7ef8e653cae53ccd127f2f79009e0d4))
* handle nullable traffic_limit_gb and end_date in subscription model ([e94b93d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/e94b93d0c10b4e61d7750ca47e1b2f888f5873ed))
* handle StaleDataError in webhook when user already deleted ([d58a80f](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/d58a80f3eaa64a6fc899e10b3b14584fb7fc18a9))
* ignore 'message is not modified' on privacy policy decline ([be1da97](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/be1da976e14a35e6cca01a7fca7529c55c1a208b))
* preserve purchased traffic when extending same tariff ([b167ed3](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/b167ed3dd1c6e6239db2bdbb8424bcb1fb7715d9))
* prevent cascading greenlet errors after sync rollback ([a1ffd5b](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/a1ffd5bda6b63145104ce750835d8e6492d781dc))
* protect server counter callers and fix tariff change detection ([bee4aa4](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/bee4aa42842b8b6611c7c268bcfced408a227bc0))
* suppress 'message is not modified' error in updates panel ([3a680b4](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/3a680b41b0124848572809d187cab720e1db8506))
* use callback fallback when MINIAPP_CUSTOM_URL is not set ([eaf3a07](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/eaf3a07579729031030308d77f61a5227b796c02))
* use flush instead of commit in server counter functions ([6cec024](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/6cec024e46ef9177cb59aa81590953c9a75d81bb))

## [3.10.0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.9.1...v3.10.0) (2026-02-10)


### New Features

* add all remaining RemnaWave webhook events (node, service, crm, device) ([1e37fd9](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/1e37fd9dd271814e644af591343cada6ab12d612))
* add close button to all webhook notifications ([d9de15a](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/d9de15a5a06aec3901415bdfd25b55d2ca01d28c))
* add MULENPAY_WEBSITE_URL setting for post-payment redirect ([fe5f5de](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/fe5f5ded965e36300e1c73f25f16de22f84651ad))
* add RemnaWave incoming webhooks for real-time subscription events ([6d67cad](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/6d67cad3e7aa07b8490d88b73c38c4aca6b9e315))
* handle errors.bandwidth_usage_threshold_reached_max_notifications webhook ([8e85e24](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/8e85e244cb786fb4c06162f2b98d01202e893315))
* handle service.subpage_config_changed webhook event ([43a326a](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/43a326a98ccc3351de04d9b2d660d3e7e0cb0efc))
* unified notification delivery for webhook events (email + WS support) ([26637f0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/26637f0ae5c7264c0430487d942744fd034e78e8))
* webhook protection — prevent sync/monitoring from overwriting webhook data ([184c52d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/184c52d4ea3ce02d40cf8a5ab42be855c7c7ae23))


### Bug Fixes

* add action buttons to webhook notifications and fix empty device names ([7091eb9](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/7091eb9c148aaf913c4699fc86fef5b548002668))
* add missing placeholders to Arabic SUBSCRIPTION_INFO template ([fe54640](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/fe546408857128649930de9473c7cde1f7cc450a))
* allow non-HTTP deep links in crypto link webhook updates ([f779225](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/f77922522a85b3017be44b5fc71da9c95ec16379))
* build composite device name from platform + hwid short suffix ([17ce640](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/17ce64037f198837c8f2aa7bf863871f60bdf547))
* downgrade transient API errors (502/503/504) to warning level ([ec8eaf5](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/ec8eaf52bfdc2bde612e4fc0324575ba7dc6b2e1))
* extract device name from nested hwidUserDevice object ([79793c4](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/79793c47bbbdae8b0f285448d5f70e90c9d4f4b0))
* preserve payment initiation time in transaction created_at ([90d9df8](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/90d9df8f0e949913f09c4ebed8fe5280453ab3ab))
* security and architecture fixes for webhook handlers ([dc1e96b](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/dc1e96bbe9b4496e91e9dea591c7fc0ef4cc245b))
* stop CryptoBot webhook retry loop and save cabinet payments to DB ([2cb6d73](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/2cb6d731e96cbfc305b098d8424b84bfd6826fb4))
* sync subscription status from panel in user.modified webhook ([5156d63](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/5156d635f0b5bc0493e8f18ce9710cca6ff4ffc8))
* use event field directly as event_name (already includes scope prefix) ([9aa22af](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/9aa22af3390a249d1b500d75a7d7189daaed265e))
* webhook:close button not working due to channel check timeout ([019fbc1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/019fbc12b6cf61d374bbed4bce3823afc60445c9))

## [3.9.1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.9.0...v3.9.1) (2026-02-10)


### Bug Fixes

* don't delete Heleket invoice message on status check ([9943253](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/994325360ca7665800177bfad8f831154f4d733f))
* safe HTML preview truncation and lazy-load subscription fallback ([40d8a6d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/40d8a6dc8baf3f0f7c30b0883898b4655a907eb5))
* use actual DB columns for subscription fallback query ([f0e7f8e](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/f0e7f8e3bec27d97a3f22445948b8dde37a92438))

## [3.9.0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.8.0...v3.9.0) (2026-02-09)


### New Features

* add lite mode functionality with endpoints for retrieval and update ([7b0403a](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/7b0403a307702c24efefc5c14af8cb2fb7525671))
* add Persian (fa) locale with complete translations ([29a3b39](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/29a3b395b6e67e4ce2437b75120b78c76b69ff4f))
* allow tariff deletion with active subscriptions ([ebd6bee](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/ebd6bee05ed7d9187de9394c64dfd745bb06b65a))
* **localization:** add Persian (fa) locale support and wire it across app flows ([cc54a7a](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/cc54a7ad2fb98fe6e662e1923027f4989ae72868))


### Bug Fixes

* nullify payment FK references before deleting transactions in user restoration ([0b86f37](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/0b86f379b4e55e499ca3d189137e2aed865774b5))
* prevent sync from overwriting end_date for non-ACTIVE panel users ([49871f8](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/49871f82f37d84979ea9ec91055e3f046d5854be))
* promo code max_uses=0 conversion and trial UX after promo activation ([1cae713](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/1cae7130bc87493ab8c7691b3c22ead8189dab55))
* skip users with active subscriptions in admin inactive cleanup ([e79f598](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/e79f598d17ffa76372e6f88d2a498accf8175c76))
* use selection.period.days instead of selection.period_days ([4541016](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/45410168afe683675003a1c41c17074a54ce04f1))


### Performance

* cache logo file_id to avoid re-uploading on every message ([142ff14](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/142ff14a502e629446be7d67fab880d12bee149d))


### Refactoring

* remove "both" mode from BOT_RUN_MODE, keep only polling and webhook ([efa3a5d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/efa3a5d4579f24dabeeba01a4f2e981144dd6022))
* remove Flask, use FastAPI exclusively for all webhooks ([119f463](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/119f463c36a95685c3bc6cdf704e746b0ba20d56))
* remove smart auto-activation & activation prompt, fix production bugs ([a3903a2](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/a3903a252efdd0db4b42ca3fd6771f1627050a7f))

## [3.8.0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.7.2...v3.8.0) (2026-02-08)


### New Features

* add admin device management endpoints ([c57de10](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/c57de1081a9e905ba191f64c37221c36713c82a6))
* add admin traffic packages and device limit management ([2f90f91](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/2f90f9134df58b8c0a329c20060efcf07d5d92f9))
* add admin updates endpoint for bot and cabinet releases ([11b8ab1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/11b8ab1959e83fafe405be0b76dfa3dd1580a68b))
* add endpoint for updating user referral commission percent ([da6f746](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/da6f746b093be8cdbf4e2889c50b35087fbc90de))
* add enrichment data to CSV export ([f2dbab6](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/f2dbab617155cdc41573d885f0e55222e5b9825b))
* add server-side sorting for enrichment columns ([15c7cc2](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/15c7cc2a58e1f1935d10712a981466629db251d1))
* add system info endpoint for admin dashboard ([02c30f8](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/02c30f8e7eb6ba90ed8983cfd82199a22b473bbf))
* add traffic usage enrichment endpoint with devices, spending, dates, last node ([5cf3f2f](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/5cf3f2f76eb2cd93282f845ea0850f6707bfcc09))
* admin panel enhancements & bug fixes ([e6ebf81](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/e6ebf81752499df8eb0a710072785e3d603dba33))


### Bug Fixes

* add debug logging for bulk device response structure ([46da31d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/46da31d89c55c225dec9136d225f2db967cf8961))
* add email field to traffic table for OAuth/email users ([94fcf20](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/94fcf20d17c54efd67fa7bd47eff1afdd1507e08))
* add email/UUID fallback for OAuth user panel sync ([165965d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/165965d8ea60a002c061fd75f88b759f2da66d7d))
* add enrichment device mapping debug logs ([5be82f2](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/5be82f2d78aed9b54d74e86f261baa5655e5dcd9))
* include additional devices in tariff renewal price and display ([17e9259](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/17e9259eb1d41dbf1d313b6a7d500f6458359393))
* paginate bulk device endpoint to fetch all HWID devices ([4648a82](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/4648a82da959410603c92055bcde7f96131e0c29))
* read bot version from pyproject.toml when VERSION env is not set ([9828ff0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/9828ff0845ec1d199a6fa63fe490ad3570cf9c8f))
* revert device pagination, add raw user data field discovery ([8f7fa76](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/8f7fa76e6ab34a3ad2f61f4e1f06026fd3fbf4e3))
* use bulk device endpoint instead of per-user calls ([5f219c3](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/5f219c33e6d49b0e3e4405a57f8344a4237f1002))
* use correct pagination params (start/size) for bulk HWID devices ([17af51c](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/17af51ce0bdfa45197384988d56960a1918ab709))
* use per-user panel endpoints for reliable device counts and last node data ([9d39901](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/9d39901f78ece55c740a5df2603601e5d0b1caca))

## [3.7.2](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.7.1...v3.7.2) (2026-02-08)


### Bug Fixes

* handle FK violation in create_yookassa_payment when user is deleted ([55d281b](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/55d281b0e37a6e8977ceff792cccb8669560945b))
* remove dots from Remnawave username sanitization ([d6fa86b](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/d6fa86b870eccbf22327cd205539dd2084f0014e))

## [3.7.1](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.7.0...v3.7.1) (2026-02-08)


### Bug Fixes

* release-please config — remove blocked workflow files ([d88ca98](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/d88ca980ec67e303e37f0094a2912471929b4cef))
* remove workflow files and pyproject.toml from release-please extra-files ([5070bb3](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/5070bb34e8a09b2641783f5e818bb624469ad610))
* resolve HWID reset and webhook FK violation ([5f3e426](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/5f3e426750c2adcb097b92f1a9e7725b1c5c5eba))
* resolve HWID reset context manager bug and webhook FK violation ([a9eee19](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/a9eee19c95efdc38ecf5fa28f7402a2bbba7dd07))
* resolve merge conflict in release-please config ([0ef4f55](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/0ef4f55304751571754f2027105af3e507f75dfd))
* resolve multiple production errors and performance issues ([071c23d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/071c23dd5297c20527442cb5d348d498ebf20af4))

## [3.7.0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.6.0...v3.7.0) (2026-02-07)


### Features

* add admin traffic usage API ([aa1cd38](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/aa1cd3829c5c3671e220d49dd7ec2d83563e2cf9))
* add admin traffic usage API with per-node statistics ([6c2c25d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/6c2c25d2ccb27446c822e4ed94d9351bfeaf4549))
* add node/status filters and custom date range to traffic page ([ad260d9](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/ad260d9fe0b232c9d65176502476212902909660))
* add node/status filters, custom date range, connected devices to traffic page ([9ea533a](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/9ea533a864e345647754f316bd27971fba1420af))
* add node/status filters, date range, devices to traffic page ([ad6522f](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/ad6522f547e68ef5965e70d395ca381b0a032093))
* add risk columns to traffic CSV export ([7c1a142](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/7c1a1426537e43d14eff0a1c3faeca484611b58b))
* add tariff filter, fix traffic data aggregation ([fa01819](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/fa01819674b2d2abb0d05b470559b09eb43abef8))
* node/status filters + custom date range for traffic page ([a161e2f](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/a161e2f904732b459fef98a67abfaae1214ecfd4))
* tariff filter + fix traffic data aggregation ([1021c2c](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/1021c2cdcd07cf2194e59af7b59491108339e61f))
* traffic filters, date range & risk columns in CSV export ([4c40b5b](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/4c40b5b370616a9ab40cbf0cccdbc0ac4a3f8278))


### Bug Fixes

* close unclosed HTML tags in version notification ([0b61c7f](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/0b61c7fe482e7bbfbb3421307a96d54addfd91ee))
* close unclosed HTML tags when truncating version notification ([b674550](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/b6745508da861af9b2ff05d89b4ac9a3933da510))
* correct response parsing for non-legacy node-users endpoint ([a076dfb](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/a076dfb5503a349450b5aa8aac3c6f40070b715d))
* correct response parsing for non-legacy node-users endpoint ([91ac90c](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/91ac90c2aecfb990679b3d0c835314dde448886a))
* handle mixed types in traffic sort ([eeed2d6](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/eeed2d6369b07860505c59bcff391e7b17e0ffb7))
* handle mixed types in traffic sort for string fields ([a194be0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/a194be0843856b3376167d9ba8a8ef737280998c))
* resolve 429 rate limiting on traffic page ([b12544d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/b12544d3ea8f4bbd2d8c941f83ee3ac412157adb))
* resolve 429 rate limiting on traffic page ([924d6bc](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/924d6bc09c815c1d188ea1d0e7974f7e803c1d3f))
* use legacy per-node endpoint for traffic aggregation ([cc1c8ba](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/cc1c8bacb42a9089021b7ae0fecd1f2717953efb))
* use legacy per-node endpoint with correct response format ([b707b79](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/b707b7995b90c6465910a35e9a4403e1408c6568))
* use PaymentService for cabinet YooKassa payments ([61bb8fc](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/61bb8fcafd94509568f134ccdba7769b66cc7d5d))
* use PaymentService for cabinet YooKassa payments to save local DB record ([ff5bba3](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/ff5bba3fc5d1e1b08d008b64215e487a9eb70960))

## [3.6.0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.5.0...v3.6.0) (2026-02-07)


### Features

* add OAuth 2.0 authorization (Google, Yandex, Discord, VK) ([97be4af](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/97be4afbffd809fe2786a6d248fc4d3f770cb8cf))
* add panel info, node usage endpoints and campaign to user detail ([287a43b](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/287a43ba6527ff3464a527821d746a68e5371bbe))
* add panel info, node usage endpoints and campaign to user detail ([0703212](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/070321230bcb868e4bc7a39c287ed3431a4aef4a))
* add TRIAL_DISABLED_FOR setting to disable trial by user type ([c4794db](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/c4794db1dd78f7c48b5da896bdb2f000e493e079))
* add user_id filter to admin tickets endpoint ([8886d0d](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/8886d0dea20aa5a31c6b6f0c3391b3c012b4b34d))
* add user_id filter to admin tickets endpoint ([d3819c4](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/d3819c492f88794e4466c2da986fd3a928d7f3df))
* block registration with disposable email addresses ([9ca24ef](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/9ca24efe434278925c0c1f8d2f2d644a67985c89))
* block registration with disposable email addresses ([116c845](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/116c8453bb371b5eacf5c9d07f497eb449a355cc))
* disable trial by user type (email/telegram/all) ([4e7438b](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/4e7438b9f9c01e30c48fcf2bbe191e9b11598185))
* migrate OAuth state storage from in-memory to Redis ([e9b98b8](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/e9b98b837a8552360ef4c41f6cd7a5779aa8b0a7))
* OAuth 2.0 authorization (Google, Yandex, Discord, VK) ([3cbb9ef](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/3cbb9ef024695352959ef9a82bf8b81f0ba1d940))
* return 30-day daily breakdown for node usage ([7102c50](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/7102c50f52d583add863331e96f3a9de189f581a))
* return 30-day daily breakdown for node usage ([e4c65ca](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/e4c65ca220994cf08ed3510f51d9e2808bb2d154))


### Bug Fixes

* increase OAuth HTTP timeout to 30s ([333a3c5](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/333a3c590120a64f6b2963efab1edd861274840c))
* parse bandwidth stats series format for node usage ([557dbf3](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/557dbf3ebe777d2137e0e28303dc2a803b15c1c6))
* parse bandwidth stats series format for node usage ([462f7a9](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/462f7a99b9d5c0b7436dbc3d6ab5db6c6cfa3118))
* pass tariff object instead of tariff_id to set_tariff_promo_groups ([1ffb8a5](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/1ffb8a5b85455396006e1fcddd48f4c9a2ca2700))
* query per-node legacy endpoint for user traffic breakdown ([b94e3ed](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/b94e3edf80e747077992c03882119c7559ad1c31))
* query per-node legacy endpoint for user traffic breakdown ([51ca3e4](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/51ca3e42b75c1870c76a1b25f667629855cfe886))
* reduce node usage to 2 API calls to avoid 429 rate limit ([c68c4e5](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/c68c4e59846abba9c7c78ae91ec18e2e0e329e3c))
* reduce node usage to 2 API calls to avoid 429 rate limit ([f00a051](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/f00a051bb323e5ba94a3c38939870986726ed58e))
* use accessible nodes API and fix date format for node usage ([943e9a8](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/943e9a86aaa449cd3154b0919cfdc52d2a35b509))
* use accessible nodes API and fix date format for node usage ([c4da591](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/c4da59173155e2eeb69eca21416f816fcbd1fa9c))

## [3.5.0](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/compare/v3.4.0...v3.5.0) (2026-02-06)


### Features

* add tariff reorder API endpoint ([4c2e11e](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/4c2e11e64bed41592f5a12061dcca74ce43e0806))
* pass platform-level fields from RemnaWave config to frontend ([095bc00](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/095bc00b33d7082558a8b7252906db2850dce9da))
* serve original RemnaWave config from app-config endpoint ([43762ce](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/43762ce8f4fa7142a1ca62a92b97a027dab2564d))
* tariff reorder API endpoint ([085a617](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/085a61721a8175b3f4fd744614c446d73346f2b7))


### Bug Fixes

* enforce blacklist via middleware ([561708b](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/561708b7772ec5b84d6ee049aeba26dc70675583))
* enforce blacklist via middleware instead of per-handler checks ([966a599](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/966a599c2c778dce9eea3c61adf6067fb33119f6))
* exclude signature field from Telegram initData HMAC validation ([5b64046](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/5b6404613772610c595e55bde1249cdf6ec3269d))
* improve button URL resolution and pass uiConfig to frontend ([0ed98c3](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/0ed98c39b6c95911a38a26a32d0ffbcf9cfd7c80))
* restore unquote for user data parsing in telegram auth ([c2cabbe](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/c2cabbee097a41a95d16c34d43ab7e70d076c4dc))


### Reverts

* remove signature pop from HMAC validation ([4234769](https://github.com/BEDOLAGA-DEV/remnawave-bedolaga-telegram-bot/commit/4234769e92104a6c4f8f1d522e1fca25bc7b20d0))
