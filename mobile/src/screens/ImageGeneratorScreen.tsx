import React, { useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Image,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import Toast from 'react-native-toast-message';
import { apiBaseUrl, apiClient, getApiErrorMessage, visionToolsEnabled } from '../lib/api';

const DISABLED_MESSAGE =
  'The generator is wired for mobile, but your current personal preset keeps backend image generation off until you explicitly enable it.';

const ImageGeneratorScreen = () => {
  const [prompt, setPrompt] = useState('');
  const [steps, setSteps] = useState('30');
  const [loading, setLoading] = useState(false);
  const [generatedImage, setGeneratedImage] = useState('');
  const [statusText, setStatusText] = useState(DISABLED_MESSAGE);

  const parsedSteps = useMemo(() => {
    const value = parseInt(steps, 10);
    if (Number.isNaN(value)) {
      return 30;
    }
    return Math.max(10, Math.min(value, 60));
  }, [steps]);

  const handleGenerate = async () => {
    if (!visionToolsEnabled) {
      Toast.show({
        type: 'info',
        text1: 'Generator is off',
        text2: DISABLED_MESSAGE,
      });
      return;
    }

    if (!prompt.trim()) {
      Toast.show({
        type: 'error',
        text1: 'Add a prompt',
        text2: 'Describe the image you want to generate.',
      });
      return;
    }

    setLoading(true);
    try {
      const response = await apiClient.post<{ image: string; format: string }>(
        '/api/image/generate',
        {
          prompt,
          num_inference_steps: parsedSteps,
        }
      );
      setGeneratedImage(`data:image/png;base64,${response.data.image}`);
      setStatusText('Image generation is active for this app build.');
      Toast.show({
        type: 'success',
        text1: 'Image ready',
        text2: 'The backend returned a generated image.',
      });
    } catch (error) {
      const message = getApiErrorMessage(error, 'Could not generate image');
      setStatusText(message);
      Toast.show({
        type: 'error',
        text1: 'Generation failed',
        text2: message,
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.section}>
        <Text style={styles.helperText}>API: {apiBaseUrl}</Text>
        <Text style={styles.title}>Image Generator</Text>
        <Text style={styles.description}>
          This screen is now wired end to end, but it stays conservative by default so it does not change your daily local setup without your say-so.
        </Text>
      </View>

      <View style={styles.noticeCard}>
        <Text style={styles.noticeTitle}>
          {visionToolsEnabled ? 'Mobile vision is enabled for this app build.' : 'Ready, but held back by default.'}
        </Text>
        <Text style={styles.noticeBody}>{statusText}</Text>
      </View>

      <View style={styles.formCard}>
        <Text style={styles.label}>Prompt</Text>
        <TextInput
          style={styles.textArea}
          placeholder="Describe the image you want..."
          placeholderTextColor="#98a2b3"
          value={prompt}
          onChangeText={setPrompt}
          multiline
          numberOfLines={5}
        />

        <Text style={styles.label}>Inference Steps</Text>
        <TextInput
          style={styles.input}
          value={steps}
          onChangeText={setSteps}
          keyboardType="numeric"
        />

        <TouchableOpacity
          style={[styles.generateButton, loading && styles.buttonDisabled]}
          onPress={handleGenerate}
          disabled={loading}
        >
          {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.generateButtonText}>Generate Image</Text>}
        </TouchableOpacity>
      </View>

      {generatedImage ? (
        <View style={styles.resultCard}>
          <Text style={styles.resultTitle}>Generated Preview</Text>
          <Image source={{ uri: generatedImage }} style={styles.generatedImage} />
          <Text style={styles.resultCaption}>
            Prompt: {prompt}
          </Text>
        </View>
      ) : (
        <View style={styles.placeholderCard}>
          <Text style={styles.placeholderText}>
            No generated image yet. Once enabled, this screen will render the backend PNG preview here.
          </Text>
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f4f6fb',
  },
  content: {
    padding: 16,
    gap: 14,
  },
  section: {
    gap: 6,
  },
  helperText: {
    fontSize: 12,
    color: '#667085',
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#102132',
  },
  description: {
    fontSize: 15,
    lineHeight: 22,
    color: '#475467',
  },
  noticeCard: {
    padding: 16,
    borderRadius: 18,
    backgroundColor: '#fff4e8',
    borderWidth: 1,
    borderColor: '#f2d2a4',
    gap: 6,
  },
  noticeTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#102132',
  },
  noticeBody: {
    fontSize: 14,
    lineHeight: 20,
    color: '#344054',
  },
  formCard: {
    padding: 18,
    borderRadius: 22,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#dde3ea',
    gap: 10,
  },
  label: {
    fontSize: 15,
    fontWeight: '700',
    color: '#102132',
  },
  textArea: {
    minHeight: 120,
    padding: 12,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#d0d5dd',
    backgroundColor: '#f8fafc',
    textAlignVertical: 'top',
    color: '#102132',
  },
  input: {
    padding: 12,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#d0d5dd',
    backgroundColor: '#f8fafc',
    color: '#102132',
  },
  generateButton: {
    marginTop: 8,
    paddingVertical: 14,
    borderRadius: 16,
    backgroundColor: '#b54708',
    alignItems: 'center',
  },
  generateButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '700',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  resultCard: {
    padding: 18,
    borderRadius: 22,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#dde3ea',
    gap: 12,
  },
  resultTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#102132',
  },
  generatedImage: {
    width: '100%',
    height: 320,
    borderRadius: 18,
    backgroundColor: '#e4e7ec',
  },
  resultCaption: {
    color: '#475467',
    lineHeight: 20,
  },
  placeholderCard: {
    padding: 18,
    borderRadius: 22,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#dde3ea',
  },
  placeholderText: {
    color: '#667085',
    lineHeight: 20,
  },
});

export default ImageGeneratorScreen;
