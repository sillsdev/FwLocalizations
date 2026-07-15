**Localizations for FieldWorks**

The authoritative list of supported languages is maintained at https://crowdin.com/project/fieldworks/settings#translations. To add a new language, you will also need to update the following locations in the FieldWorks repository (https://github.com/sillsdev/fieldworks):
- Build/Installer.targets (CopyFilesToInstall, HarvestAllL10ns)
- FLExInstaller/CustomComponents.wxi (multiple places)
- FLExInstaller/CustomFeatures.wxi
- ¿Others?
  1. A search for “zh” in fwrepo/fw/Build and fwrepo/fw/FLExInstaller should reveal all of these lists
  2. In other places, we build the list dynamically using something like `<LocaleDirs Include="$([System.IO.Directory]::GetDirectories(&quot;$(L10nsDirectory)&quot;))"/>` (these do not need to be updated)

- Linux localization package specifications need regenerated for new localizations to be shipped:

  1. Checkout the latest localization files.

          cd ~/fwrepo/fw/Localizations
          git fetch
          git checkout origin/develop

  2. Generate l10n package specifications.

          cd ~/fwrepo/debian
          git fetch
          git checkout origin/release/9.0 # Or similar release branch.
          ./generate-l10n-control-entries ../fw

  3. Merge in changes, and push the result.

          meld control-l10n control

**Removing or adding strings**

If you remove strings from FieldWorks you will need to get your system ready to run the `uploadUpdatesForTranslation` build target.

1. Make sure that you have liblcm cloned locally, checked out to the right branch, and specified in your `LibraryDevelopment.properties` file.
2. Set the `CROWDIN_API_KEY` environment variable to a Crowdin personal access token (Crowdin API v2 — `overcrowdin` is built on `Crowdin.Api` v2, which authenticates with a personal access token; the "version 1" project API key this step used to reference no longer exists) for an account with access to the FieldWorks Crowdin project.
3. `build /t:uploadUpdatesForTranslation`

This uploads `lists/LocalizableLists.xml` (and other localizable sources) to the `"latest"` branch of the Crowdin project, per FieldWorks' `crowdin.json`. Note that this repo's own `.github/workflows/fetch-crowdin.yml` downloads translations from the `"FieldWorks-9.0"` branch instead — check which branch your change needs to reach before assuming an upload or download is visible on the other side.

**Semantic domain lists have independent copies elsewhere**

`lists/LocalizableLists.xml` is the Crowdin source for semantic domain names, descriptions, and questions, but several other repos hold their own static copies of the same English text that are *not* regenerated when this file changes and must be updated by hand:
- liblcm: `src/SIL.LCModel/Templates/SemDom.xml`
- TheCombine: `deploy/scripts/semantic_domains/xml/SemanticDomains-*.xml`
- webonary: `localizations/input/LocalizedLists-*.xml`
- This repo's own root `LocalizedLists-*.xml` files

If you edit the English text in `lists/LocalizableLists.xml`, check whether those copies need the same edit.
