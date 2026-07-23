## Localizations for FieldWorks

The authoritative list of supported languages is maintained at https://crowdin.com/project/fieldworks/settings#translations. To add a new language, you will also need to update its entries in the [FieldWorks](https://github.com/sillsdev/fieldworks) repository. The installer is mid-migration from WiX 3 to WiX 6, so each locale is duplicated across parallel files; a search for a locale code such as “zh” across `Build/` and `FLExInstaller/` reliably reveals all of them. Currently:

- `Build/Installer.targets` and `Build/Installer.legacy.targets` — the `L10nFiles` item group (locale output folders)
- `FLExInstaller/CustomComponents.wxi` and `FLExInstaller/wix6/CustomComponents.wxi` — several places each (directory, `WixVariable`s, harvest include)
- `FLExInstaller/CustomFeatures.wxi` and `FLExInstaller/wix6/CustomFeatures.wxi` — the per-language `<Feature>` list

## Removing or adding strings

If you remove strings from FieldWorks you will need to get your system ready to run the `uploadUpdatesForTranslation` build target.

1. Make sure that you have liblcm cloned locally, checked out to the right branch, and specified in your `LibraryDevelopment.properties` file.
2. Set the `CROWDIN_API_KEY` environment variable to a Crowdin personal access token (Crowdin API v2 — `overcrowdin` is built on `Crowdin.Api` v2, which authenticates with a personal access token) for an account with access to the FieldWorks Crowdin project.
3. `build /t:uploadUpdatesForTranslation`

This uploads `lists/LocalizableLists.xml` (and other localizable sources) to the `"latest"` branch of the Crowdin project, per FieldWorks' `crowdin.json`. Check which branch your change needs to reach before assuming an upload or download is visible on the other side.

## Semantic domain lists have independent copies elsewhere

`lists/LocalizableLists.xml` is the Crowdin source for semantic domain names, descriptions, and questions, but several other repos hold their own static copies of the same text that are _not_ regenerated when this file changes and must be updated by hand:

- [liblcm](https://github.com/sillsdev/liblcm): `src/SIL.LCModel/Templates/SemDom.xml`
- [TheCombine](https://github.com/sillsdev/TheCombine/): `deploy/scripts/semantic_domains/xml/SemanticDomains-*.xml`
- [webonary](https://github.com/sillsdev/webonary): `localizations/input/LocalizedLists-*.xml`
- This repo's own root `LocalizedLists-*.xml` files

If you edit the English text in `lists/LocalizableLists.xml`, check whether those copies need the same edit.
