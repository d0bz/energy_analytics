<?php
header('Content-Type: application/json');

// Configuration
$uploadDir = 'uploads/';
$pythonScript = 'simulation_grid_battery_vanilla.py';

// Create uploads directory if it doesn't exist
if (!file_exists($uploadDir)) {
    mkdir($uploadDir, 0777, true);
}

try {
    if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
        throw new Exception('Only POST method is allowed');
    }

    if (!isset($_FILES['file'])) {
        throw new Exception('No file uploaded');
    }

    $file = $_FILES['file'];
    if ($file['error'] !== UPLOAD_ERR_OK) {
        throw new Exception('File upload failed with error code ' . $file['error']);
    }

    // Validate file type
    $mimeType = mime_content_type($file['tmp_name']);
    if ($mimeType !== 'text/csv' && $mimeType !== 'text/plain') {
        throw new Exception('Invalid file type. Only CSV files are allowed.');
    }

    // Create a unique filename
    $timestamp = time();
    $uploadedFile = $uploadDir . $timestamp . '_' . basename($file['name']);
    
    // Move uploaded file
    if (!move_uploaded_file($file['tmp_name'], $uploadedFile)) {
        throw new Exception('Failed to move uploaded file');
    }

    // Get parameters
    $startDate = !empty($_POST['start_date']) ? $_POST['start_date'] : '';
    $endDate = !empty($_POST['end_date']) ? $_POST['end_date'] : '';
    $inverterPower = !empty($_POST['inverter_power']) ? intval($_POST['inverter_power']) : 200;
    $batteryCapacity = !empty($_POST['battery_capacity']) ? intval($_POST['battery_capacity']) : 600;
    $efficiencyLoss = !empty($_POST['efficiency_loss']) ? intval($_POST['efficiency_loss']) : 12;
    $batteryReserve = !empty($_POST['battery_reserve']) ? intval($_POST['battery_reserve']) : 10;
    $efficiency = (100 - $efficiencyLoss) / 100;
    $reserve = (100 - $batteryReserve/2) / 100;

    // Build command with all parameters
    $command = sprintf(
        'python3 %s %s --inverter %d --battery %d --efficiency %.2f --reserve %.2f',
        escapeshellarg($pythonScript),
        escapeshellarg($uploadedFile),
        $inverterPower,
        $batteryCapacity,
        $efficiency,
        $reserve
    );

    // Add date parameters if provided
    if (!empty($startDate) && !empty($endDate)) {
        $command .= sprintf(
            ' --start %s --end %s',
            escapeshellarg($startDate),
            escapeshellarg($endDate)
        );
    }

    // Execute simulation
    $output = [];
    $returnVar = 0;
    exec($command, $output, $returnVar);

    if ($returnVar !== 0) {
        throw new Exception('Simulation failed: ' . implode("\n", $output));
    }

    // Read simulation results
    $resultFile = 'simulation_output.csv';
    if (!file_exists($resultFile)) {
        throw new Exception('Simulation output file not found');
    }

    $simulationData = file_get_contents($resultFile);
    
    // Clean up
    //unlink($uploadedFile);

    // Return success response with data
    echo json_encode([
        'success' => true,
        'data' => base64_encode($simulationData)
    ]);

} catch (Exception $e) {
    http_response_code(400);
    echo json_encode([
        'success' => false,
        'error' => $e->getMessage()
    ]);
}
?>
