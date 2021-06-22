# -*- coding: utf-8 -*-
from rasp_audio_stream import AudioInputStream
from pqg_phasescope import PQGPhaseScope


# PyAudioストリーム入力取得クラス
ais = AudioInputStream(CHUNK=1024) #, input_device_keyword="Real")
# フェイズスコープ用クラス
phasescope = PQGPhaseScope( (ais.CHANNELS, ais.CHUNK) )

# AudioInputStreamは別スレッドで動かす
import threading
thread = threading.Thread(target=ais.run, args=(phasescope.callback_sigproc,))
thread.daemon=True
thread.start()

# フェイズスコープ起動
phasescope.run_app()