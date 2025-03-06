# Running the DREAM-RNN container with a sample dataset

To run a test prediction using the DREAM-RNN container and sample Evaluator container:

1. Download the containers from Zenodo: https://zenodo.org/records/14861069

```bash
mkdir DREAMRNN
mkdir test_evaluator
```

```bash
cd DREAMRNN
wget https://zenodo.org/records/14861069/files/predictor.sif?download=1
mv predictor.sif?download=1 predictor.sif
```

``` bash
cd test_evaluator
wget https://zenodo.org/records/14861069/files/evaluator.sif?download=1
mv evaluator.sif?download=1 evaluator.sif
wget https://zenodo.org/records/14861069/files/evaluator_data.zip?download=1
mv evaluator_data.zip?include_deleted=0 evaluator_data
mkdir predictions
```

Note: if you run into issues downloading the `evaluator_data` folder you may need to manually download it off Zenodo. 

2. Get the IP Address of where the Predictor is running

Note: PORTs above 5000 are usually free to use

`hostname -I`

3. Start the DREAMRNN Predictor with the IP address and PORT arguments

`apptainer run predictor.sif HOST PORT`

Example:
`apptainer run predictor.sif 172.16.47.243 5000`

4. Start the test Evaluator 

```bash 
apptainer run \ 
    -B /path/to/evaluator_data:/evaluator_data  \
    -B /path/to/predictions:/predictions  \
    evaluator.sif HOST PORT /predictions
```
Example:
```bash 
apptainer run \ 
    -B /path/to/evaluator_data:/evaluator_data  \
    -B /path/to/predictions:/predictions  \
    evaluator.sif 172.16.47.243 5000 /predictions
```

The `-B` mounts local directories so that the Evaluator container can read in the JSON file from a local folder and write the prediction to the locally created `/predictions` folder.

5. If the Evaluator-Prediction communication was successful a JSON file will be found in the `predictions/` folder.

Yay! You just completed a successful communication between the DREAMRNN model and a test sequence set with GAME :)

```bash
{
    "request": "predict",
    "prediction_tasks": [
        {
            "name": "gosai_synthetic_sequences",
            "type_requested": "expression",
            "type_actual": "expression",
            "cell_type_requested": "K562",
            "cell_type_actual": "K562",
            "scale_prediction_requested": "linear",
            "scale_prediction_actual": "log",
            "species_requested": "homo_sapiens",
            "species_actual": "homo_sapiens",
            "predictions": {
                "7:70038969:G:T:A:wC": [
                    -0.4900762140750885
                ],
                "1:192696196:C:T:A:wC": [
                    -0.4205487370491028
                ],
                "1:211209457:C:T:A:wC": [
                    -0.2514425814151764
                ],
                "15:89574440:GT:G:A:wC": [
                    1.1541708707809448
                ],
                "15:89574440:GT:G:R:wC": [
                    1.1637296676635742
                ]
            }
        }
    ]
```
    