# HACS Default Repository PR Checklist

Use this checklist before submitting a PR to [`hacs/default`](https://github.com/hacs/default) to add this integration.

- [ ] repository is public
- [ ] issues enabled
- [ ] description set
- [ ] topics set
- [ ] HACS Action passed
- [ ] Hassfest passed
- [ ] GitHub release exists
- [ ] hacs.json includes name and country
- [ ] brand/icon.png exists
- [ ] brand/icon@2x.png exists
- [ ] entry added alphabetically to hacs/default integration file

## Instructions

1. Fork `https://github.com/hacs/default`
2. Clone your fork locally
3. Create a branch from `master` (do not use `master` directly)
4. Edit `integration` file — add a line for `cesar_smart` in alphabetical order:
   ```
   roblencheg/cesar-smart-hass
   ```
5. Commit with message: `Add cesar_smart integration`
6. Push to your fork
7. Create PR to `hacs/default`:
   - Title: `Add cesar_smart integration`
   - Ensure "Allow edits by maintainers" is checked
8. Wait for HACS Action and Hassfest checks to pass on the PR

## Notes

- PR can only be submitted by the repository owner or a major contributor
- The repo must already have passing HACS Action and Hassfest before the PR
- GitHub release must exist (not just a git tag)
- If the integration is country-restricted, `hacs.json` must contain `"country": ["RU"]`
