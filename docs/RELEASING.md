# Creating a release

## 1. Set the version

Edit `VERSION`, for example:

```text
4.1.0
```

## 2. Test

```bash
python -m unittest discover -s tests -v
```

## 3. Commit and push

```bash
git add .
git commit -m "Release 4.1.0"
git push
```

## 4. Create the version tag

```bash
git tag v4.1.0
git push origin v4.1.0
```

The `Build Installers` workflow builds all three deployment packages and creates a GitHub Release automatically.

For a build without creating a release, run **Actions → Build Installers → Run workflow**. The files will be available as workflow artifacts.
