## Localizations for [FieldWorks](https://github.com/sillsdev/FieldWorks)

The authoritative list of supported languages is maintained at https://crowdin.com/project/fieldworks/settings#translations. To add a new language, you will also need to update its entries in the [FieldWorks](https://github.com/sillsdev/fieldworks) repository. The installer is mid-migration from WiX 3 to WiX 6, so each locale is duplicated across parallel files; a search for a locale code such as “zh” across `Build/` and `FLExInstaller/` reliably reveals all of them. Currently:

- `Build/Installer.targets` and `Build/Installer.legacy.targets` — the `L10nFiles` item group (locale output folders)
- `FLExInstaller/CustomComponents.wxi` and `FLExInstaller/wix6/CustomComponents.wxi` — several places each (directory, `WixVariable`s, harvest include)
- `FLExInstaller/CustomFeatures.wxi` and `FLExInstaller/wix6/CustomFeatures.wxi` — the per-language `<Feature>` list

This repository no longer holds checked-in localizations (those are in Crowdin and archived as this repository's GitHub Releases). It serves as a repository of tools to facilitate localization and as a staging area for Crowdin uploads and downloads. Instructions are in [this Google document](https://docs.google.com/document/d/1Xt3mAyU-42QfunzkSJgePIP9brHFVv5pmcmiCT-zQ6A).

## Removing or adding strings

If you remove strings from FieldWorks you will need to get your system ready and run the `uploadUpdatesForTranslation` build target.

1. Make sure that you have liblcm cloned locally, checked out to the right branch, and set the `LcmRootDir` environment variable to the path of that clone.
2. Clone this repository (FwLocalizations) into the FieldWorks repo root as `Localizations` (so the path is `<FieldWorks>/Localizations`; see [FieldWorks `CONTRIBUTING.md`](https://github.com/sillsdev/FieldWorks/blob/main/Docs/CONTRIBUTING.md#optional-clone-fwlocalizations-for-translation-work)). The build reads its `lists/` sources from there and writes generated files (`*.xlf`, `messages.pot`, `LCM/`, `l10ns/`) back into it.
3. Set the `CROWDIN_API_KEY` environment variable to a Crowdin personal access token (Crowdin API v2 — `overcrowdin` is built on `Crowdin.Api` v2, which authenticates with a personal access token) for an account with access to the FieldWorks Crowdin project.
4. From the FieldWorks repo root, run `.\build.ps1 -Target uploadUpdatesForTranslation`

This uploads `lists/LocalizableLists.xml` (and other localizable sources) to the `"latest"` branch of the Crowdin project, per FieldWorks' `crowdin.json`. Check which branch your change needs to reach before assuming an upload or download is visible on the other side.

## Semantic Domains and other lists have independent copies elsewhere

`lists/LocalizableLists.xml` is the Crowdin source for semantic domain names, descriptions, and questions, but several other repos hold their own static copies of the same text that are _not_ regenerated when this file changes and must be updated by hand:

- [semdom.org](https://semdom.org/) (the authoritative version)
- [liblcm](https://github.com/sillsdev/liblcm): `src/SIL.LCModel/Templates/SemDom.xml` (the English version packaged with FieldWorks)
- [TheCombine](https://github.com/sillsdev/TheCombine/): `deploy/scripts/semantic_domains/xml/SemanticDomains-*.xml` (FieldWorks can roundtrip data to TheCombine)
- [webonary](https://github.com/sillsdev/webonary): `localizations/input/LocalizedLists-*.xml` (FieldWorks can upload data to Webonary)

If you edit the English text in `lists/LocalizableLists.xml`, check whether those copies need the same edit.

Other lists represented in `lists/LocalizableLists.xml` come from multiple other files. The Google document linked above has instructions for regenerating `lists/LocalizableLists.xml` from these lists.
