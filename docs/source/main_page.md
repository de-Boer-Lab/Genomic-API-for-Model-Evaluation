GAME was designed for the functional genomics community to create seamless communication across pre-trained models and genomics datasets. It is a product of the feedback from many model and dataset experts and our hope is that it allows for long-lasting benchmarking of models. Models and datasets communicate via a set of predefined protocols through REST APIs. The common protocol enables any model to communicate with any dataset (although not all combinations may make sense).

The evaluators (dataset APIs) will make prediction requests in the standard format to the predictors (model APIs), which then return the predictions to the Evaluator in a standard format, enabling the evaluators to calculate the model’s performance. Each of the evaluators and predictors will be containerized using Apptainer.

```{image} API.png
:alt: Diagram
```

::::{grid} 1 1 2 3 :gutter: 2

:::{grid-item-card} :link: FAQ :link-type: doc
Install alphagenome locally.
:::

:::{grid-item-card} :link: Installation :link-type: doc
The tutorials walk through example usage of the AlphaGenome model.
:::

:::{grid-item-card} :link: Reference :link-type: doc
Reference documentation for the alphagenome package.
:::

::::