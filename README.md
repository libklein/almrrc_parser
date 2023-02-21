# ALMRCC Parser

A parser for the data of the [ALMRCC challenge](https://routingchallenge.mit.edu/). You can download the dataset at [Open Data](https://registry.opendata.aws/amazon-last-mile-challenges/).

```python
from almrrc_parser import parse as parse_amazon_data
from pathlib import Path

routes, travel_times = parse_amazon_data(route_data_path=Path("almrrc2021/almrrc2021-data-evaluation/model_apply_inputs/eval_route_data.json"), package_data_path=Path("almrrc2021/almrrc2021-data-evaluation/model_apply_inputs/eval_package_data.json"), travel_time_data_path=Path("almrrc2021/almrrc2021-data-evaluation/model_apply_inputs/eval_travel_times.json"), sequence_data_path=Path("almrrc2021/almrrc2021-data-evaluation/model_score_inputs/eval_actual_sequences.json"))
```
