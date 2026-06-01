import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  TextInput,
  ActivityIndicator,
} from 'react-native';
import Toast from 'react-native-toast-message';
import { apiBaseUrl, apiClient, getApiErrorMessage } from '../lib/api';

const TextGeneratorScreen = () => {
  const [prompt, setPrompt] = useState('');
  const [maxLength, setMaxLength] = useState(256);
  const [temperature, setTemperature] = useState(0.6);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('');

  const handleGenerate = async () => {
    if (!prompt.trim()) {
      Toast.show({
        type: 'error',
        text1: 'Error',
        text2: 'Please enter a prompt',
      });
      return;
    }

    setLoading(true);
    try {
      const response = await apiClient.post('/api/text/generate', {
        prompt,
        max_length: maxLength,
        temperature,
      });
      setResult(response.data.generated_text);
      Toast.show({
        type: 'success',
        text1: 'Success',
        text2: 'Text generated successfully',
      });
    } catch (error) {
      Toast.show({
        type: 'error',
        text1: 'Error',
        text2: getApiErrorMessage(error, 'Failed to generate text'),
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    // Copy to clipboard
    Toast.show({
      type: 'success',
      text1: 'Copied',
      text2: 'Text copied to clipboard',
    });
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.section}>
        <Text style={styles.helperText}>API: {apiBaseUrl}</Text>
        <Text style={styles.label}>Prompt</Text>
        <TextInput
          style={styles.input}
          placeholder="Enter your prompt here..."
          value={prompt}
          onChangeText={setPrompt}
          multiline
          numberOfLines={6}
          placeholderTextColor="#999"
        />
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>Max Length: {maxLength}</Text>
        <View style={styles.sliderContainer}>
          <TextInput
            style={styles.sliderInput}
            value={String(maxLength)}
            onChangeText={(val) => setMaxLength(parseInt(val) || 256)}
            keyboardType="numeric"
          />
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>Temperature: {temperature.toFixed(2)}</Text>
        <View style={styles.sliderContainer}>
          <TextInput
            style={styles.sliderInput}
            value={temperature.toFixed(2)}
            onChangeText={(val) => setTemperature(parseFloat(val) || 0.6)}
            keyboardType="decimal-pad"
          />
        </View>
      </View>

      <TouchableOpacity
        style={[styles.button, loading && styles.buttonDisabled]}
        onPress={handleGenerate}
        disabled={loading}
      >
        {loading ? (
          <ActivityIndicator color="#fff" />
        ) : (
          <Text style={styles.buttonText}>Generate</Text>
        )}
      </TouchableOpacity>

      {result && (
        <View style={styles.resultSection}>
          <Text style={styles.resultTitle}>Generated Text</Text>
          <View style={styles.resultBox}>
            <Text style={styles.resultText}>{result}</Text>
          </View>
          <TouchableOpacity style={styles.copyButton} onPress={handleCopy}>
            <Text style={styles.copyButtonText}>Copy to Clipboard</Text>
          </TouchableOpacity>
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 16,
  },
  section: {
    marginBottom: 20,
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  helperText: {
    fontSize: 12,
    color: '#667085',
    marginBottom: 8,
  },
  input: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    fontSize: 14,
    color: '#333',
    textAlignVertical: 'top',
  },
  sliderContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  sliderInput: {
    flex: 1,
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#e0e0e0',
    fontSize: 14,
    color: '#333',
  },
  button: {
    backgroundColor: '#667eea',
    borderRadius: 8,
    padding: 16,
    alignItems: 'center',
    marginBottom: 20,
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  resultSection: {
    marginTop: 20,
  },
  resultTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  resultBox: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#667eea',
    marginBottom: 12,
  },
  resultText: {
    fontSize: 14,
    color: '#333',
    lineHeight: 20,
  },
  copyButton: {
    backgroundColor: '#667eea',
    borderRadius: 8,
    padding: 12,
    alignItems: 'center',
  },
  copyButtonText: {
    color: '#fff',
    fontSize: 14,
    fontWeight: '600',
  },
});

export default TextGeneratorScreen;
