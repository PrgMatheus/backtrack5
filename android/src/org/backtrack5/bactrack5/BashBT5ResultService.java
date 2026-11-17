package org.backtrack5.bactrack5;

import android.app.IntentService;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Bundle;

public class BashBT5ResultService extends IntentService {

    public BashBT5ResultService() {
        super("BashBT5ResultService");
    }

    @Override
    protected void onHandleIntent(Intent intent) {
        if (intent == null) return;

        Bundle result = intent.getBundleExtra("result");
        if (result == null) return;

        SharedPreferences preferences =
            getSharedPreferences("bashbt5_termux", MODE_PRIVATE);

        preferences.edit()
            .putString("stdout", result.getString("stdout", ""))
            .putString("stderr", result.getString("stderr", ""))
            .putString("errmsg", result.getString("errmsg", ""))
            .putInt("exitCode", result.getInt("exitCode", -1))
            .putInt("err", result.getInt("err", 0))
            .putInt("execution_id",
                intent.getIntExtra("execution_id", -1))
            .putBoolean("result_ready", true)
            .apply();
    }
}
