**Localizations for FieldWorks**

The authoritative list of supported languages is maintained at https://crowdin.com/project/fieldworks/settings#translations. To add a new language, you will also need to update the following locations in the FieldWorks repository (https://github.com/sillsdev/fieldworks):
- Build/Installer.targets (CopyFilesToInstall, HarvestAllL10ns)
- FLExInstaller/CustomComponents.wxi (multiple places)
- FLExInstaller/CustomFeatures.wxi
- ¿Others?
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
