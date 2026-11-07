# M157.38 AutocompleteMatch constructor repair

- Failed run: https://github.com/nojirokaimo-svg/android-browser-dev-tk/actions/runs/42310590826
- Failed job: `128296437005` (`continue-1`)
- Compiler location: `components/omnibox/browser/android/java/src/org/chromium/components/omnibox/AutocompleteMatch.java:211`
- Cause: patch 200 supplied one extra `null` before the M157 `fillIntoEdit` argument.
- Old measured source SHA-256: `75e8366462f2f5212016be67f1fb4f329cd0a31620ded50857e7141abddd11fc`
- Corrected source SHA-256: `514e14cfa414e1b1ec3ae22e8a545f6ca080033ef34291a831ed29430b3259f9`
- Exact resume checkpoint: `kiwi-15738-264139f4b8d5dc63ce8240d683ef3e40818b1731-42310590826-1-continue-1`

The migration is gated by the complete old file digest and verifies the complete corrected digest. It cannot modify an unknown source file.
