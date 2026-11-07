#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_LIS3DH.h>

const uint8_t SD_CHIP_SELECT = 10;
const uint8_t LIS3DH_ADDRESS = 0x18;

const uint16_t LOG_RATE_HZ = 200;
const uint32_t SAMPLE_INTERVAL_US = 1000000UL / LOG_RATE_HZ;
const uint16_t FLUSH_EVERY_SAMPLES = 50;        // Flush every 0.25 s at 200 Hz.
const float STANDARD_GRAVITY = 9.80665F;

Adafruit_LIS3DH lis = Adafruit_LIS3DH();
File logFile;

char logFilename[] = "BUNG00.CSV";
uint32_t nextSampleUs = 0;
uint32_t loggingStartUs = 0;
uint16_t samplesSinceFlush = 0;
uint32_t missedDeadlines = 0;

void fatalError(const __FlashStringHelper *message) {
    Serial.println(message);
    if (logFile) {
        logFile.flush();
        logFile.close();
    }

    // Stop here. Rapid messages in Serial Monitor indicate an error.
    while (true) {
        Serial.println(message);
        delay(1000);
    }
}

bool openNewLogFile() {
    // Use an 8.3-format filename for maximum SD-library compatibility.
    for (uint8_t runNumber = 0; runNumber < 100; runNumber++) {
        logFilename[4] = '0' + (runNumber / 10);
        logFilename[5] = '0' + (runNumber % 10);

        if (!SD.exists(logFilename)) {
            logFile = SD.open(logFilename, FILE_WRITE);
            return (bool)logFile;
        }
    }
    return false;
}

void setup() {
    Serial.begin(115200);
    delay(250);

    Serial.println(F("Bungee acceleration logger starting..."));

    Wire.begin();

    if (!lis.begin(LIS3DH_ADDRESS)) {
        fatalError(F("ERROR: LIS3DH not detected. Check VIN, GND, SDA, and SCL."));
    }

    // The lab limit is 7 g. The 16 g range leaves margin for short impact peaks.
    lis.setRange(LIS3DH_RANGE_16_G);
    lis.setDataRate(LIS3DH_DATARATE_400_HZ);
    lis.setPerformanceMode(LIS3DH_MODE_HIGH_RESOLUTION);

    // Pin 10 is the SD-card chip-select pin on Adafruit shield Product 1141.
    pinMode(SD_CHIP_SELECT, OUTPUT);
    if (!SD.begin(SD_CHIP_SELECT)) {
        fatalError(F("ERROR: SD card initialization failed."));
    }

    if (!openNewLogFile()) {
        fatalError(F("ERROR: Could not create BUNG00.CSV-BUNG99.CSV."));
    }

    // Metadata lines begin with # so analysis software can identify/skip them.
    logFile.println(F("# MEAM 3470 bungee acceleration test"));
    logFile.println(F("# LIS3DH range_g=16,sensor_rate_hz=400,log_rate_hz=200"));

logFile.println(F("elapsed_us,ax_mps2,ay_mps2,az_mps2,a_magnitude_mps2,a_magnitude_g,missed_deadlines"));
    logFile.flush();

    Serial.print(F("Logging to "));
    Serial.println(logFilename);
    Serial.println(F("Logging begins in 3 seconds."));
    delay(3000);

    loggingStartUs = micros();
    nextSampleUs = loggingStartUs;
}

void loop() {
    uint32_t nowUs = micros();

    // Signed subtraction makes this comparison safe across micros() rollover.
    if ((int32_t)(nowUs - nextSampleUs) < 0) {
        return;
    }

    // If an SD write delayed us by more than one interval, record that fact and
    // resume from the present instead of rapidly writing duplicate samples.
    if ((uint32_t)(nowUs - nextSampleUs) >= SAMPLE_INTERVAL_US) {
        missedDeadlines += (nowUs - nextSampleUs) / SAMPLE_INTERVAL_US;
        nextSampleUs = nowUs;
    }
    nextSampleUs += SAMPLE_INTERVAL_US;

    sensors_event_t event;
    lis.getEvent(&event);

    const float ax = event.acceleration.x;
    const float ay = event.acceleration.y;
    const float az = event.acceleration.z;
    const float magnitude = sqrt(ax * ax + ay * ay + az * az);

    // Unsigned subtraction also remains correct if micros() rolls over once.
    logFile.print(nowUs - loggingStartUs);
    logFile.print(',');
    logFile.print(ax, 4);
    logFile.print(',');
    logFile.print(ay, 4);
    logFile.print(',');
    logFile.print(az, 4);
    logFile.print(',');
    logFile.print(magnitude, 4);
    logFile.print(',');
    logFile.print(magnitude / STANDARD_GRAVITY, 4);
    logFile.print(',');
    logFile.println(missedDeadlines);

    samplesSinceFlush++;
    if (samplesSinceFlush >= FLUSH_EVERY_SAMPLES) {
        logFile.flush();
        samplesSinceFlush = 0;
    }
}
