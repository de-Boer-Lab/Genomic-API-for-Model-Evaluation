### Design Principles for GAME Modules

- **Predictor should focus on predicting the biological signal of interest**, assay types are not provided to the models
- **Maintain a strong separation** between model prediction and evaluation
- **Enable a sustainable benchmarking framework** that supports long-term maintenance and encapsulation

#### Evaluator Responsibilites

- Evaluators are clients that are responsbile for evaluating models on specific benchmarks
- Determine what information the Predictors require for their predictions and what the best evaluation metrics are for their benchmarks

#### Predictor Responsibilities

- Predictors are servers that take a request for predictions on a set of DNA sequences and determining how it can best fulfill the request, given what the model can predict (or decline to predict if it cannot do so)

#### Communication protocol example

P: Hi my name is "Predictor"! My job is to wait and listen for a "Evaluator" to ask me to do something.

E: Hello I'm an "Evaluator"! I'm sending you a .json file, could you please predict the accessbility of these sequences?

P: Sure thing :) One moment please...

P: Psst! Hey CellMatcher! I was asked for cellX, but I have no clue that that is, can I have a little help?

CM: Sure thing! cellX is similar to your cellY, so you should use that for your predictions instead.

P: Here you go, Evaluator - i'm sending you a .json file back with all the predictions for cellY.

.. toctree::
   :maxdepth: 1
   :hidden:

   RESTAPI_methods
   Evaluator_requests
   Predictor_responses
   help
   Error_messages
   Matcher