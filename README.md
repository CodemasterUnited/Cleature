# Cleature
A lightweight, fast templating engine for `.chtml` files, with variable injection, file includes, and a clean CLI. Designed for making static site generation easy with partitions and variables.

![Python 3.7+](https://img.shields.io/badge/Python%203.7%2B-%230089FF?style=flat-square&logo=python&logoColor=white) ![MIT License](https://img.shields.io/badge/MIT%20Licensed-black?style=flat-square&labelColor=white)

---
## Table of Contents
- [What is Cleature?](#what-is-cleature)
- [Installation](#installation)
- [CLI Usage](#cli-usage)
- [Module Usage](#module-usage)
- [Notes](#notes)
- [Configuration File](#configuration-file)
- [Cleature Syntax](#cleature-syntax)
  - [File Inclusion](#file-inclusion)
  - [Variable Substitution](#variable-substitution)
  - [Constants](#constants)
  - [Syntax Example](#syntax-example)
- [Option Key Mapping](#option-key-mapping)
- [About Cleature](#about-cleature)
- [About the Author](#about-the-author)

---

## What is Cleature?
**Cleature** is a static templating engine for `.chtml` files that supports:
- Variable substitution, with different scopes – `{{ variable }}`
- Constants block that override global variables – `<constants(...) />`
- File includes to include `.chtml` and `.html` files – 
`<include("partials/footer.chtml") />`
- Clean CLI with custom configurations – `cleature render srcdir distdir [options]`
- Set custom configurations with `cleature.config.json` file.
- Usable as a CLI tool, or directly in Python code for versatility.

Use Cleature to build modular, maintainable, and portable static HTML projects with zero runtime dependencies.

---

## Installation
You can install Cleature just by running this command:
```bash
pip install cleature
```

You can check the version by running:
```bash
cleature --version
```

---

## CLI Usage

Cleature provides a clean CLI powered by Python's argparse:
```bash
cleature render <srcdir> <distdir> [options]
```

Here,
- `<srcdir>` should be the source directory in which there are `.chtml` files.
- `<distdir>` should be the output directory, where the parsed files and folders will be kept.

`<srcdir>` and `<distdir>` can be anywhere on the disk and don't need to be near each other.

### Options
- `--refresh`:
	Clear the output (distdir) before rendering.

- `--exclude <dir1> <dir2> ...`:
	Skip one or more directories inside srcdir.

- `--debug`:
	Enable debug logs.

- `--variables a=x b=y ...`:
	Modify or add variables in `key=value` pairs that will be substituted.

### Example
Here is a simple example of using Cleature:
```bash
cleature render ./src ./out --refresh --exclude temp drafts --debug --variables sitename=Foo author=Bar
```

This will:
- Render all `.chtml` files from `./src`
- Save output HTML to `./out`
- Skip `temp` and `drafts` directories and the files inside it.
- Clean the output folder first.
- Enable debug logging.

---

## Module Usage
Cleature can also be used as a regular Python module:
```bash
from cleature.core import render
from pathlib import Path

render(
    src_directory=Path("src"),
    dist_directory=Path("dist"),
    provided_options={
        "refresh_dist": True,
        "excluded_dirs": ["drafts", "temp"],
        "debug": True,
        "variables": {
            "title": "Hello from Python!"
        }
    }
)
```

Perfect for use in:
- Web backends
- Build pipelines
- CI/CD workflows
- Custom automation scripts

---

## Notes
- Only `<srcdir>` and `<distdir>` are required, and the options are optional.
- The recommended way to provide the options is via the `cleature.config.json` file.
- The options provided via the `cleature.config.json` file, have less priority than the options provided via the CLI or Python module.
- The options key (or names) are different and simple in case of CLI, but same for the `cleature.config.json` file and module options.
- All the paths (except the `<distdir>` that is, the output directory) is always relative to the `<srcdir>` that is, the source directory.

---

## Configuration File
The recommended way to provide the options is through the `cleature.config.json` file. It should be kept at the **root of the SRC directory**, so that it can be detected.

```json
{
  "variables": {
    "title": "Website Title",
    "author": "John Doe",
    "year": "2025"
  },
  "excluded_dirs": ["components/"]
}
```

The options are the same, as when programmatically using the module.
Cleature will automatically detect and merge this config.

---

## Cleature Syntax
The `.chtml` files should follow this syntax, to be properly processed. The syntax is fully common HTML, as long as not any specific Cleature feature is needed.

But, for variables substitution, and includes, this is how the syntax looks:

### File Inclusion
To include a file, this line should be placed, where another file needs to be included. `<include(path/to/file.chtml)/>`

### Variable Substitution
We can set variables, using the options in CLI, module or `cleature.config.json`.

Use variables by placing them wherever needed, and they’ll be automatically substituted:
```
{{ variable_name }}
```

### Constants
You can also set file-level variables using the `<constants(...) />` block.

These are shared by the file in which they are defined, and any files included by that file.

Place them at the top of the file like this:
```
<constants(
    "page_title":"Home",
    "name": "Homepage"
)/>
```
This block also overrides the variables set by the options, but only for the file in which it is defined.

### Syntax Example

If this is the content of `index.chtml`:
```html
<constants(
    "user": "John Doe"
)/>
<include(greet.chtml)/>
<p>You are welcome to {{ site_name }}.</p>
```

And this is the content of `greet.chtml`:
```html
<h1>Hello, {{ user }}!</h1>
```

And if `site_name` variable is set as `MySite` in the options, then the output `index.html` would be like this:
```html
<h1>Hello, John Doe!</h1>
<p>You are welcome to MySite.</p>
```

Here, in the example above,
**In `index.chtml`:**
- `<constants(...) />` is used to define file level variables.
- `<include(greet.chtml)/>` is used to include the `greet.chtml` file, and evaluate it.
- `{{ site_name }}` will be evaluated to the variable named `site_name` from the variable list. (Here, we have assumed we provided `site_name` in options during rendering. Also, we could have used `cleature.config.json`)

**In `greet.chtml`:**
- `{{ user }}` will be evaluated to the value of `user` set in the `index.chtml` (i.e., the file in which this was included. This happens because file-level variables are shared by the includes.)
---
## Option Key Mapping

The keys of some options are different in CLI from its config/module key, for simplicity purposes. Both serve the same purpose. Both version of keys
are shown below:

| CLI Option | Config/Module Key |
|------------|-------------------|
|--refresh   |refresh_dist       |
|--exclude   |excluded_dirs      |
|--variables |variables          |
|--debug     |debug              |

---

## About Cleature
Cleature requires Python 3.7 and above. It doesn't need any external dependencies, or packages.

Cleature comes under MIT License — Use freely, modify, and distribute with credit.

---

## About the Author
Hey, I'm CodemasterUnited, the author of this library. I got the idea of making Cleature when I was writing the docs for ArtenoMark, which is my image watermarking API. I was struggling with the changes I had to make to all the files, just for a little theme-level change, which was very inefficient. Also, I didn't find any other simple and lightweight library that could help me in generating simple static sites. Either they were too advanced, or I didn't like their syntax. 

So, I decided to make my own simple templating engine — Cleature. Cleature may not be too advanced yet, but it fulfills the task I made it for. If there is someone like me, who also had to struggle with not finding a simple templating engine, they should check out Cleature. 

If anyone is interested in contributing to Cleature, they are most welcome. But still, I won't force anyone to use Cleature, or contribute to it. If you need it, use it. If you don't, then don't. 😁

Finally, happy coding! 🎉
