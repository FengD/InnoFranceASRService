# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Added support for configuring speaker diarization model path via environment variable `DIARIZATION_MODEL_PATH`
- Added CHANGELOG.md file to track project changes

### Changed
- Updated speaker diarization implementation to correctly extract `speaker_diarization` from pipeline output
- Implemented merging of consecutive segments from the same speaker to produce cleaner transcripts
- Improved speaker diarization accuracy by using proper model output handling

### Fixed
- Fixed issue where speaker diarization results were not correctly extracted from pipeline output
- Fixed issue where consecutive segments from the same speaker were not merged

## [1.0.0] - 2026-01-21

### Added
- Initial release of ASR Service with Speaker Diarization
- Speech-to-text (ASR) functionality based on Whisper
- Speaker diarization using PyAnnote.audio
- RESTful API interface
- Web frontend for easy use
- Logging and auditing capabilities
- Prometheus monitoring metrics