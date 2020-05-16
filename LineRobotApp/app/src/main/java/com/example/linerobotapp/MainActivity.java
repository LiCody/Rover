package com.example.linerobotapp;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;

import android.Manifest;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothDevice;
import android.bluetooth.BluetoothSocket;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.DialogInterface;
import android.content.Intent;
import android.content.IntentFilter;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Message;
import android.renderscript.ScriptGroup;
import android.util.Log;
import android.view.View;

import com.google.android.material.snackbar.Snackbar;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.net.ServerSocket;
import java.util.Set;
import java.util.UUID;

public class MainActivity extends AppCompatActivity {
    //https://developer.android.com/guide/topics/connectivity/bluetooth
    private final static int REQUEST_ENABLE_BT = 1;
    private final static String RPI_MAC_ADDRESS = "DC:A6:32:27:E5:19";
    private static final String TAG = "MainActivity";
    private final static UUID uuid = UUID.fromString("00001101-0000-1000-8000-00805F9B34FB");
    private BluetoothDevice rpi = null;
    private Handler handler;
    private BluetoothSocket socket;
    private OutputStream out;
    private BluetoothAdapter bluetoothAdapter;
    //private Snackbar error_MSG = Snackbar.make(findViewById(R.id.myCoordinatorLayout), stringId, duration);


    private interface MessageConstants {
        public static final int MESSAGE_READ = 0;
        public static final int MESSAGE_WRITE = 1;
        public static final int MESSAGE_TOAST = 2;
    }

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        try {
            bluetooth();
        } catch (Exception e) {
            e.printStackTrace();
        }

    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        unregisterReceiver(receiver);
        try {
            out.close();
            socket.close();
        } catch (IOException e) {
            e.printStackTrace();
        }

    }

    void bluetooth() throws Exception {
        this.bluetoothAdapter = BluetoothAdapter.getDefaultAdapter();
        if (bluetoothAdapter == null) {
            // Device doesn't support Bluetooth
            System.out.println("device doesnt support bluetooth go next");
            return;
        }
        if (!bluetoothAdapter.isEnabled()) {
            Intent enableBtIntent = new Intent(BluetoothAdapter.ACTION_REQUEST_ENABLE);
            startActivityForResult(enableBtIntent, REQUEST_ENABLE_BT);
        }
        if (Build.VERSION.SDK_INT > Build.VERSION_CODES.LOLLIPOP){
            int permissionCheck = this.checkSelfPermission("Manifest.permission.ACCESS_FINE_LOCATION");
            permissionCheck += this.checkSelfPermission("Manifest.permission.ACCESS_COARSE_LOCATION");
            if (permissionCheck != 0) {

                this.requestPermissions(new String[]{Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.ACCESS_COARSE_LOCATION}, 1001); //Any number
            }
        }
        // here paired devices is actually just any on the network
        Set<BluetoothDevice> pairedDevices = bluetoothAdapter.getBondedDevices();
        bluetoothAdapter.cancelDiscovery();
        Log.d(TAG, "HI");
        if (!bluetoothAdapter.startDiscovery() && !bluetoothAdapter.isDiscovering()) {
            Log.d(TAG, "Not discovering :(");
        } else {
            Log.d(TAG,"Started Discovering");
        }

        if (pairedDevices.size() > 0) {
            // There are paired devices. Get the name and address of each paired device.
            for (BluetoothDevice device : pairedDevices) {
                String deviceName = device.getName();
                String deviceHardwareAddress = device.getAddress(); // MAC address
                if (deviceHardwareAddress.equals(RPI_MAC_ADDRESS)) {
                    this.rpi = device;
                }
                System.out.println(deviceName);
                System.out.println(deviceHardwareAddress);
            }
        }

        if (this.rpi != null) {
                this.rpi.createBond();
                Method makeSocket = rpi.getClass().getMethod("createRfcommSocket", new Class[] {int.class});
                socket = (BluetoothSocket) makeSocket.invoke(rpi, 1);
                Log.d("socket"," Connecting ");
                socket.connect();
                Log.d("socket"," Connected ");
                this.out = socket.getOutputStream();
                this.out.write("Send".getBytes());
                this.out.flush();

        } else {
            IntentFilter filter = new IntentFilter(BluetoothDevice.ACTION_FOUND);
            registerReceiver(receiver, filter);
        }

        //bluetoothAdapter.cancelDiscovery(); // stop discovery to free up resources

    }

    private final BroadcastReceiver receiver = new BroadcastReceiver() {
        public void onReceive(Context context, Intent intent) {
            String action = intent.getAction();
            if (BluetoothDevice.ACTION_FOUND.equals(action)) {
                // Discovery has found a device. Get the BluetoothDevice
                // object and its info from the Intent.
                BluetoothDevice device = intent.getParcelableExtra(BluetoothDevice.EXTRA_DEVICE);
                System.out.println("Found something");
                if (device.getAddress().equals(RPI_MAC_ADDRESS)) {
                    System.out.println("Found the RPI");
                    device.createBond();
                    rpi = device;
                    Method makeSocket = null;
                    try {
                        makeSocket = rpi.getClass().getMethod("createRfcommSocket", new Class[] {int.class});
                    } catch (NoSuchMethodException e) {
                        e.printStackTrace();
                    }
                    try {
                        socket = (BluetoothSocket) makeSocket.invoke(rpi, 1);
                    } catch (IllegalAccessException | InvocationTargetException e) {
                        e.printStackTrace();
                    }
                    Log.d("socket"," Connecting ");
                    Log.d("socket"," Connected ");
                    try {
                        socket.connect();

                        out = socket.getOutputStream();
                    } catch (IOException e) {
                        e.printStackTrace();
                    }
                    bluetoothAdapter.cancelDiscovery();
                }
            }
        }
    };


    public void leftButton(View view) {
        try {
            this.out.write("Left".getBytes());
            this.out.flush();
        } catch (Exception e) {
            showError(view);
        }
    }

    public void rightButton(View view) throws IOException {
        try {
            this.out.write("Right".getBytes());
            this.out.flush();
        } catch (Exception e) {
            showError(view);
        }
    }

    public void backButton(View view) throws IOException {
        try {
            this.out.write("Back".getBytes());
            this.out.flush();
        } catch (Exception e) {
            showError(view);
        }
    }

    public void forwardsButton(View view) throws IOException {
        if (this.rpi != null) {
            this.out.write("Forwards".getBytes());
            this.out.flush();
        } else {
            showError(view);
        }
    }

    public void connectButton(View view) throws Exception {
        if (this.rpi == null) {
            bluetooth();
        }
    }

    public void stopButton(View view) throws  IOException {
        try {
            this.out.write("Stop".getBytes());
            this.out.flush();
        } catch (Exception e) {
            showError(view);
        }
    }

    public void startButton(View view) throws IOException {
        try {
            this.out.write("Start".getBytes());
            this.out.flush();
        } catch (Exception e) {
            showError(view);
        }
    }


    public void showError(View view) { //https://www.youtube.com/watch?v=hv_-tX1VwXE&list=PLgCYzUzKIBE8KHMzpp6JITZ2JxTgWqDH2&index=3
        AlertDialog.Builder error = new AlertDialog.Builder(this);
        error.setMessage("Not Connected to RaspberryPI")
                .setPositiveButton("Continue", new DialogInterface.OnClickListener() {
                    @Override
                    public void onClick(DialogInterface dialog, int which) {
                        dialog.dismiss();
                    }
                })
                .create();
        error.show();
    }
}
