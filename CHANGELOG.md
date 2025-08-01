# Changelog

## [2.4.4](https://github.com/Vatsim-Scandinavia/discord-bot/compare/v2.4.3...v2.4.4) (2025-08-01)


### Bug Fixes

* bump required Python version to 3.13 or greater ([#163](https://github.com/Vatsim-Scandinavia/discord-bot/issues/163)) ([3ab9b30](https://github.com/Vatsim-Scandinavia/discord-bot/commit/3ab9b308d4efa2afcfbbe66f1f5fb0e4ea7827c1))
* Have AFIS possitions be reported as AFIS ([#167](https://github.com/Vatsim-Scandinavia/discord-bot/issues/167)) ([5da404f](https://github.com/Vatsim-Scandinavia/discord-bot/commit/5da404f30d327fbc84087e32842acc726652ade3))


### Documentation

* add myself ([#165](https://github.com/Vatsim-Scandinavia/discord-bot/issues/165)) ([c4f697e](https://github.com/Vatsim-Scandinavia/discord-bot/commit/c4f697e5273e20026cfcd3ec21c56e31553ed4b0))

## [2.4.3](https://github.com/Vatsim-Scandinavia/discord-bot/compare/v2.4.2...v2.4.3) (2025-07-19)


### Bug Fixes

* **roles:** use laptop rather than tone-dependant technologist ([#160](https://github.com/Vatsim-Scandinavia/discord-bot/issues/160)) ([3795eba](https://github.com/Vatsim-Scandinavia/discord-bot/commit/3795ebac40bf534ad09a7af1fece9c9abdb309b9))

## [2.4.2](https://github.com/Vatsim-Scandinavia/discord-bot/compare/v2.4.1...v2.4.2) (2025-07-19)


### Bug Fixes

* **roles:** use technologist emoji ([#158](https://github.com/Vatsim-Scandinavia/discord-bot/issues/158)) ([158f795](https://github.com/Vatsim-Scandinavia/discord-bot/commit/158f795eb75ccd27afbe1d407f1daf4e7c36a5f4))

## [2.4.1](https://github.com/Vatsim-Scandinavia/discord-bot/compare/v2.4.0...v2.4.1) (2025-07-17)


### Bug Fixes

* added trained word ([#152](https://github.com/Vatsim-Scandinavia/discord-bot/issues/152)) ([60be42b](https://github.com/Vatsim-Scandinavia/discord-bot/commit/60be42b0a15d566c909e262999e9ce8bd913057d))
* correct reaction role order and better comments ([b33dd6f](https://github.com/Vatsim-Scandinavia/discord-bot/commit/b33dd6f2be7eb603fb0a2de8776ae7c4d52cc64c))
* **faq:** send embed together with message ([#149](https://github.com/Vatsim-Scandinavia/discord-bot/issues/149)) ([251a458](https://github.com/Vatsim-Scandinavia/discord-bot/commit/251a458e8d5df34930257fe2f6e15b2614ea279b))
* **roles:** add support for open tech role ([2a04a74](https://github.com/Vatsim-Scandinavia/discord-bot/commit/2a04a74e553bf8dc6c3f01abe8209024e043bdf6))


### Documentation

* **rules:** Proof Reading and Typos ([#155](https://github.com/Vatsim-Scandinavia/discord-bot/issues/155)) ([ddad6d0](https://github.com/Vatsim-Scandinavia/discord-bot/commit/ddad6d05e4f029c504452243b3d97f757b6880ca))

## [2.4.0](https://github.com/Vatsim-Scandinavia/discord-bot/compare/v2.3.3...v2.4.0) (2025-06-08)


### Features

* FAQ messages ([#147](https://github.com/Vatsim-Scandinavia/discord-bot/issues/147)) ([87470a4](https://github.com/Vatsim-Scandinavia/discord-bot/commit/87470a45f4476ec171909eab20af5422895f1829))


### Bug Fixes

* add structured logging to sync_commands ([#145](https://github.com/Vatsim-Scandinavia/discord-bot/issues/145)) ([96b03fd](https://github.com/Vatsim-Scandinavia/discord-bot/commit/96b03fdd39486e0e026dd47152e099e33cdd4e73))
* **coordination:** allow workaround to fix users nicknames ([e330fd6](https://github.com/Vatsim-Scandinavia/discord-bot/commit/e330fd6a49ff2a57715cab7b7529d907eef204fa))
* **coordination:** divide nick restoration into two reasons ([#143](https://github.com/Vatsim-Scandinavia/discord-bot/issues/143)) ([d0d7de7](https://github.com/Vatsim-Scandinavia/discord-bot/commit/d0d7de7ef7ca5f869f853d1015eb93840e28b42c))
* **coordination:** only support separator rather than prefix and suffix ([#136](https://github.com/Vatsim-Scandinavia/discord-bot/issues/136)) ([8aef274](https://github.com/Vatsim-Scandinavia/discord-bot/commit/8aef274dd44c83ee32ccb28da01e0596f9bc3bb6))
* **coordination:** prevent and log users with invalid state ([#148](https://github.com/Vatsim-Scandinavia/discord-bot/issues/148)) ([3e53593](https://github.com/Vatsim-Scandinavia/discord-bot/commit/3e535939379f0f376860cd0364ac147cbe29a5dc))
* **coordination:** update cache together with command ([#141](https://github.com/Vatsim-Scandinavia/discord-bot/issues/141)) ([fc726be](https://github.com/Vatsim-Scandinavia/discord-bot/commit/fc726be6ab3dbbe12cb4e9e35d7d55fcb9e67203))
* **roles:** add additional reasons to understand flow ([52d24df](https://github.com/Vatsim-Scandinavia/discord-bot/commit/52d24df0ccee8f00b3ef0cb06aeffcec04bd0722))
* **roles:** integrate member update and check for modified nicks ([#140](https://github.com/Vatsim-Scandinavia/discord-bot/issues/140)) ([52d24df](https://github.com/Vatsim-Scandinavia/discord-bot/commit/52d24df0ccee8f00b3ef0cb06aeffcec04bd0722))

## [2.3.3](https://github.com/Vatsim-Scandinavia/discord-bot/compare/v2.3.2...v2.3.3) (2025-04-22)


### Bug Fixes

* **coordination:** exception on duplicate prefix ([7f58a5c](https://github.com/Vatsim-Scandinavia/discord-bot/commit/7f58a5c0e0c61738b6070d50130314545d199439))
* **coordination:** remove underscores and CTR suffix ([917c604](https://github.com/Vatsim-Scandinavia/discord-bot/commit/917c604255ed2f5c44f5464b146948c6c99b1cc0))
* **coordination:** use _SUFFIX environment variable for callsign suffix ([#132](https://github.com/Vatsim-Scandinavia/discord-bot/issues/132)) ([760e3b2](https://github.com/Vatsim-Scandinavia/discord-bot/commit/760e3b22f20882d31accdef6e4e2b28966f4db65))

## [2.3.2](https://github.com/Vatsim-Scandinavia/discord-bot/compare/v2.3.1...v2.3.2) (2025-04-15)


### Bug Fixes

* **coordination:** do not update controllers with unchanged name ([#127](https://github.com/Vatsim-Scandinavia/discord-bot/issues/127)) ([4bf34bd](https://github.com/Vatsim-Scandinavia/discord-bot/commit/4bf34bd9e5b2d934f9682c1d74bc63b2559d7173))

## [2.3.1](https://github.com/Vatsim-Scandinavia/discord-bot/compare/v2.3.0...v2.3.1) (2025-04-14)


### Bug Fixes

* **coordination:** broken callsign updating due to typo ([#124](https://github.com/Vatsim-Scandinavia/discord-bot/issues/124)) ([e6e77e7](https://github.com/Vatsim-Scandinavia/discord-bot/commit/e6e77e70ed830b691ed8f133a63a5f160ee40626))

## [2.3.0](https://github.com/Vatsim-Scandinavia/discord-bot/compare/v2.2.0...v2.3.0) (2025-04-14)


### Features

* add callsign of online controllers to nicknames ([#121](https://github.com/Vatsim-Scandinavia/discord-bot/issues/121)) ([cc12018](https://github.com/Vatsim-Scandinavia/discord-bot/commit/cc120180a124656ec7d33d0695138501f5a6799a))
* allow regex for callsigns to get coordination prefix ([#121](https://github.com/Vatsim-Scandinavia/discord-bot/issues/121)) ([cc12018](https://github.com/Vatsim-Scandinavia/discord-bot/commit/cc120180a124656ec7d33d0695138501f5a6799a))
* shield callsign coordination feature behind CIDs ([#121](https://github.com/Vatsim-Scandinavia/discord-bot/issues/121)) ([cc12018](https://github.com/Vatsim-Scandinavia/discord-bot/commit/cc120180a124656ec7d33d0695138501f5a6799a))
