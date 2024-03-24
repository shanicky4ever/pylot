import json
import os

import erdos

class PredictionLoggerOperator(erdos.Operator):
    def __init__(self, prediction_stream: erdos.ReadStream,
                 finished_indicator_stream: erdos.WriteStream, flags,
                 file_base_name):
        prediction_stream.add_callback(self.on_prediction_update)
        self._flags = flags
        self._file_base_name = file_base_name
        self._msg_cnt = 0
        self._data_path = os.path.join(self._flags.data_path, file_base_name)
        os.makedirs(self._data_path, exist_ok=True)

    @staticmethod
    def connect(prediction_stream: erdos.ReadStream):
        finished_indicator_stream = erdos.WriteStream()
        return [finished_indicator_stream]

    def on_prediction_update(self, msg: erdos.Message):
        self._msg_cnt += 1
        if self._msg_cnt % self._flags.log_every_nth_message != 0:
            return
        transfor_predictions = [pred.predicted_trajectory for pred in msg.predictions]
        assert len(msg.timestamp.coordinates) == 1
        timestamp = msg.timestamp.coordinates[0]
        file_name = os.path.join(self._data_path,
                                 'predictions-{}.json'.format(timestamp))
        with open(file_name, 'w') as outfile:
            json.dump(self._get_log_format(transfor_predictions), 
                      outfile, indent=4, separators=(',', ': '))
    
    def _get_log_format(self, prediction):
        return [[{
            'x': pred_t.location.x,
            'y': pred_t.location.y,
        } for pred_t in pred] for pred in prediction]
    