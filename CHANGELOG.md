# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.4] - 2023-06-02
### Changed
 - Added `.dockerignore`.
 - Added mimetype support for `.map` and `.woff` files.

## [0.0.3] - 2023-05-30
### Changed
- Repository content is now left as bytes (previously we were getting the
  `text`), wrapped in `io.BytesIO`, and sent back to the client with
  `send_file()`. This allows fetching images, which previously did not survive
  conversion to text.
- The content-fetching endpoint will now rewrite URLs that end with `/` to
  `/index.html`, mimicking the behavior of GitHub Pages or a typical webserver
  configuration.

## [0.0.2] - 2023-05-23
### Changed
- Reworked GitHub API interaction to use the raw content type (by passing the
  `Accept: application/vnd.github.raw` header). This allows fetching files
  larger than 1MB ([GitHub docs on size limit]).

[GitHub docs on size limit]: https://docs.github.com/en/rest/reference/repos#size-limits

## [0.0.1] - 2023-02-19
Initial release.

[0.0.4]: https://github.com/sclabs/private-ghp/compare/v0.0.3...v0.0.4
[0.0.3]: https://github.com/sclabs/private-ghp/compare/v0.0.2...v0.0.3
[0.0.2]: https://github.com/sclabs/private-ghp/compare/v0.0.1...v0.0.2
[0.0.1]: https://github.com/sclabs/private-ghp/releases/tag/v0.0.1
