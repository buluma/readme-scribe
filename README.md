# readme-scribe

A GitHub Action that automatically generates & updates markdown content (like your README.md)

## Instructions

1. Create a [markscribe](https://github.com/muesli/markscribe) template and
place it anywhere in a repository that you automatically want to update. In this
guide we will use `templates/README.md.tpl`.

You can find an example template that I use to automatically update my GitHub
profile here: https://github.com/muesli/markscribe/blob/master/templates/github-profile.tpl

2. In order to access some of GitHub's API, you need to provide a valid GitHub
token as a secret called `PERSONAL_GITHUB_TOKEN`. You can create a new token by
going to your profile settings:

`Developer settings` > `Personal access tokens` > `Generate new token`

Depending on your template you will need access to different API scopes. If you
want to support the full set of features, tick the checkboxes next to these
scopes: `read:user`, `repo:status`, `public_repo`, `read:org`. Check out the
[markscribe](https://github.com/muesli/markscribe) documentation for a detailed
list of required scopes for each individual template function.

Now create a new secret in your repository's `Settings` and enter that token.

3. Create a new GitHub workflow in your repository: `.github/workflows/readme-scribe.yml`

```yml
name: Update README

on:
  push:
  schedule:
    - cron: "0 */1 * * *"

jobs:
  markscribe:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@master

      - uses: muesli/readme-scribe@master
        env:
          GITHUB_TOKEN: ${{ secrets.PERSONAL_GITHUB_TOKEN }}
        with:
          template: "templates/README.md.tpl"
          writeTo: "README.md"

      - uses: stefanzweifel/git-auto-commit-action@v4
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          commit_message: Update generated README
          branch: main
          commit_user_name: readme-scribe 🤖
          commit_user_email: actions@github.com
          commit_author: readme-scribe 🤖 <actions@github.com>
```

Careful: if you use `master` instead of `main` as the default branch, you will
need to update the above config for `git-auto-commit-action` accordingly.

This action will be triggered once per hour, parses `templates/README.md.tpl`
and generates a new `README.md` for you, and eventually pushes the changes to
the `master` branch. Make sure to adjust the input values `template` and
`writeTo` to suit your needs.

## Example output

![readme-scribe example output](https://github.com/muesli/readme-scribe/raw/master/assets/template_example.png)

## Numbered contribution grid

The `generate contribution grid` workflow renders a dark contribution calendar
with daily counts, month/day labels, and a green intensity legend. It runs daily
at 01:00 UTC and can also be run from **Actions → generate contribution grid →
Run workflow**. Scheduled runs begin when the workflow is on the default branch.
The implementation branch also generates the image when its generator changes.

Generated files are published only to the separate `contribution-grid` branch;
the snake workflow continues using its existing `png` output branch.

```markdown
![Contributions](https://raw.githubusercontent.com/buluma/readme-scribe/contribution-grid/contributions.svg)
```

The generator uses `MY_GITHUB_TOKEN` when configured, otherwise the workflow's
built-in token. Counts reflect the contributions visible to that token. Publishing
uses the built-in token with `contents: write` permission.

To generate locally with Python 3 (no packages required):

```sh
GH_TOKEN="$(gh auth token)" python3 scripts/generate_contribution_grid.py --user buluma
```

For an offline render, pass `--input response.json` with a saved GitHub GraphQL
response. The default output is `dist/contributions.svg`; use `--output` to change it.
