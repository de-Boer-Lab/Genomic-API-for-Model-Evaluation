# GAME: Genomic API for Model Evaluation

GAME was designed for the functional genomics community to create seamless communication across pre-trained models and genomics datasets. It is a product of the feedback from many model and dataset experts and our hope is that it allows for long-lasting benchmarking of models. Models and datasets communicate via a set of predefined protocols through REST APIs. The common protocol enables any model to communicate with any dataset (although not all combinations may make sense).

The evaluators (dataset APIs) will make prediction requests in the standard format to the predictors (model APIs), which then return the predictions to the Evaluator in a standard format, enabling the evaluators to calculate the model’s performance. Each of the evaluators and predictors will be containerized using Apptainer.

```{image} images/API.png
:alt: Diagram
```

## What’s different from existing approaches

- **Community-driven API** design, support, maintenance, and updates.
- **Containerized workflows** to prevent dependency installation and compatibility problems.
- **Preserved model integrity** by eliminating the need for model architectural rewrites or refactoring.
<!-- - Models and Datasets are **maintained and updated by the community**  -->

## Getting Started

:::::{grid} 3

::::{grid-item-card}
:link: API/index
:link-type: doc

Explore the API Specifications
:::

::::

::::{grid-item-card} 
:link: Using_prebuilt_containers 
:link-type: doc

Get started with pre-built containers

::::

::::{grid-item-card}
:link: Building_Modules/index
:link-type: doc

Contribute your own modules to GAME

::::

:::::

If you use GAME for your research, please cite our [preprint on bioRxiv](https://www.biorxiv.org/content/10.1101/2025.07.04.663250v1.full).

Feel free to reach out via email: [ishika.luthra@ubc.ca](mailto:ishika.luthra@ubc.ca)
