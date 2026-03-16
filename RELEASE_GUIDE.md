# Release guide

## Целевой релизный контур

- GitHub-репозиторий: `https://github.com/Maxi-online/maxapi-sdk`
- PyPI distribution name: `maxapi-sdk`
- Python import path: `maxapi`
- Публикация выполняется только по тегу формата `v*`

## Что уже настроено

- `.github/workflows/tests.yml` — тесты и проверка сборки;
- `.github/workflows/publish.yml` — валидация, сборка артефактов, публикация в PyPI и создание GitHub Release по тегу `v*`.

## Что нужно настроить один раз

### GitHub

- Создать публичный репозиторий `Maxi-online/maxapi-sdk`.
- Убедиться, что default branch выбран корректно.
- У workflow должен быть доступ к `contents: write` для создания GitHub Release.

### PyPI

- Войти в аккаунт PyPI и создать проект первой публикацией имени `maxapi-sdk`.
- Добавить Trusted Publisher для репозитория `Maxi-online/maxapi-sdk`.
- Указать workflow file: `.github/workflows/publish.yml`.
- Environment name: `pypi`.

## Preflight перед первым релизом

1. Проверить, что имя `maxapi-sdk` свободно в GitHub и PyPI.
2. Проверить metadata в `pyproject.toml`.
3. Проверить README как long description.
4. Убедиться, что версия синхронизирована в:
   - `pyproject.toml`
   - `README.md`
   - `CHANGELOG.md`

## Как выпустить релиз

### 1. Запустить локальную проверку

```bash
pytest -q
python -m build
twine check dist/*
```

### 2. Создать commit и tag

```bash
git add .
git commit -m "Release 0.12.2"
git tag v0.12.2
git push origin HEAD
git push origin v0.12.2
```

### 3. Проверить workflow

После push тега GitHub Actions выполнит:

- тесты и package validation;
- сборку wheel и sdist;
- публикацию в PyPI через Trusted Publishing;
- создание GitHub Release с артефактами из `dist/`.
