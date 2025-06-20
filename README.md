# Marker-SageMaker: Supercharged Document Conversion

This is a fork of the original **[marker](https://github.com/datalab-to/marker)**, the incredibly fast and accurate document conversion tool. This version is customized to integrate with a private, high-performance **Qwen 2.5 VL 72B** model hosted on [HTX](https://www.htx.gov.sg/) servers via Amazon SageMaker.

By combining Marker's state-of-the-art layout detection with a powerful, custom-hosted multimodal LLM, this fork unlocks next-level accuracy for even the most complex documents.



## Core Marker Features
Marker is a powerhouse for document conversion, and this fork retains all its impressive capabilities:

-   Converts PDF, image, PPTX, DOCX, XLSX, HTML, and EPUB files in all languages.
-   Performs structured extraction using a JSON schema.
-   Flawlessly formats tables, forms, equations, inline math, links, and code blocks.
-   Extracts and saves images from documents.
-   Intelligently removes headers, footers, and other artifacts.
-   Fully extensible with your own logic and formatting.
-   Leverages GPU, CPU, or MPS for processing.
-   **Now with support for custom SageMaker endpoints!**

## Performance
Marker stands out for its speed and accuracy, outperforming many cloud services and open-source tools.

<img src="https://raw.githubusercontent.com/datalab-to/marker/master/data/images/overall.png" width="800px"/>

These benchmarks show Marker's impressive performance on single-page tasks. In batch mode, its throughput is even higher, capable of processing over 100 pages per second on high-end hardware.

## Hybrid Mode with Qwen 2.5 VL on SageMaker

For maximum accuracy, you can use the `--use_llm` flag. This version is specifically configured to leverage a powerful **Qwen 2.5 VL 72B** model. This enhances Marker's already excellent output by:

*   Merging complex tables that span multiple pages.
*   Accurately converting handwritten notes and inline math.
*   Intelligently extracting values from structured forms.
*   *And much more, thanks to the multimodal capabilities of Qwen 2.5!*

<img src="https://raw.githubusercontent.com/datalab-to/marker/master/data/images/table.png" width="400px"/>

As shown in the original benchmarks, using an LLM provides a significant accuracy boost over Marker alone. With Qwen 2.5 VL, the quality is pushed even further.

---

## Installation

You'll need Python 3.10+ and PyTorch. If you don't have a GPU, you may need to install the CPU version of PyTorch first. See the [PyTorch website](https://pytorch.org/get-started/locally/) for details.

Install with:```shell
pip install marker-pdf
```
To process formats other than PDF, install the full dependencies:
```shell
pip install marker-pdf[full]
```

## Usage

### Configuration for SageMaker
To use the custom Qwen 2.5 VL model, you need to configure your AWS credentials. The `SagemakerService` is designed to load these from a `.env` file in your project root.

Create a `.env` file with the following content:

```
SAGEMAKER_AWS_ACCESS_KEY_ID="YOUR_AWS_ACCESS_KEY"
SAGEMAKER_AWS_SECRET_ACCESS_KEY="YOUR_AWS_SECRET_KEY"
```

The AWS region and SageMaker endpoint name are pre-configured in the service file but can be modified as needed.

### Running a Conversion with SageMaker
To run a conversion using the new SageMaker service, specify the custom service class using the `--llm_service` flag.

```shell
marker_single /path/to/your/document.pdf --use_llm --llm_service marker.services.custom.SagemakerService
```

**(Note:** This command assumes you have placed the provided `SagemakerService` code into a file at `marker/services/custom.py`.)

### General Options
This fork supports all of Marker's original command-line options:
-   `--page_range TEXT`: Specify pages to process (e.g., "1,5-10,22").
-   `--output_format [markdown|json|html]`: Set the output format.
-   `--output_dir PATH`: Define where to save the output files.
-   `--force_ocr`: Force OCR on the entire document.
-   `--debug`: Enable debug mode for detailed logs.
-   And many more! Use `--help` to see the full list.

---

## LLM Services
When using the `--use_llm` flag, you can choose from several services. This fork adds a new one to the list:

-   **SageMaker (HTX Custom)**: **(New in this fork!)** Connects to a custom-hosted Qwen 2.5 VL 72B model on SageMaker.
    -   **Usage**: `--llm_service marker.services.custom.SagemakerService`
    -   **Configuration**: Requires `SAGEMAKER_AWS_ACCESS_KEY_ID` and `SAGEMAKER_AWS_SECRET_ACCESS_KEY` to be set as environment variables (e.g., in a `.env` file).

-   `Gemini`: Uses the Google Gemini API. Requires `--gemini_api_key`.
-   `Google Vertex`: Uses Google Vertex AI. Requires `--vertex_project_id`.
-   `Ollama`: Connects to local models via Ollama. Configure with `--ollama_base_url` and `--ollama_model`.
-   `Claude`: Uses the Anthropic Claude API. Requires `--claude_api_key`.
-   `OpenAI`: Supports any OpenAI-compatible endpoint. Configure with `--openai_api_key`, `--openai_model`, and `--openai_base_url`.

The remaining sections of the original README, including **Commercial Usage**, **Hosted API**, **Community**, **Internals**, **Troubleshooting**, **Benchmarks**, and more, can be found in the [original repository](https://github.com/datalab-to/marker). This fork is focused on the integration of the custom SageMaker service.
