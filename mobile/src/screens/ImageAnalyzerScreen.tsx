import React, { useState } from 'react';
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
import * as ImagePicker from 'expo-image-picker';
import Toast from 'react-native-toast-message';
import { apiBaseUrl, apiClient, getApiErrorMessage, visionToolsEnabled } from '../lib/api';

type AnalysisMatch = {
  label: string;
  score: number;
};

type DominantColor = {
  hex: string;
  share: number;
};

type ImageAnalysisResponse = {
  description: string;
  analysis_method?: string;
  top_matches?: AnalysisMatch[];
  dominant_colors?: DominantColor[];
  operator_assist?: {
    summary?: string;
    surface_type?: string | null;
    code_language?: string | null;
    workspace_query?: string | null;
    debug_signals?: string[];
    action_reason?: string | null;
    next_steps?: string[];
    suggested_action?: {
      id: string;
      label: string;
      command_preview?: string;
    } | null;
    workspace_context?: {
      results?: Array<{
        relative_path: string;
        snippet?: string;
      }>;
    } | null;
  };
  ocr?: {
    status: string;
    engine?: string;
    summary?: string;
    text_preview?: string;
    word_count?: number;
    average_confidence?: number | null;
  };
  ui?: {
    status: string;
    summary?: string;
    surface_type?: string | null;
    platform_hint?: string | null;
    theme?: string | null;
    panel_estimate?: number | null;
    density_label?: string | null;
    code_language?: string | null;
    layout_clues?: string[];
    readable_targets?: string[];
  };
  image_size?: {
    width: number;
    height: number;
    orientation: string;
  };
};

const DEFAULT_DISABLED_MESSAGE =
  'Vision tools are wired for mobile now, but they stay disabled by default. Set EXPO_PUBLIC_ENABLE_VISION_TOOLS=1 when you want to turn them on.';

function guessMimeType(uri: string) {
  const lowered = uri.toLowerCase();
  if (lowered.endsWith('.png')) {
    return 'image/png';
  }
  if (lowered.endsWith('.webp')) {
    return 'image/webp';
  }
  return 'image/jpeg';
}

const ImageAnalyzerScreen = () => {
  const [selectedAsset, setSelectedAsset] = useState<ImagePicker.ImagePickerAsset | null>(null);
  const [loading, setLoading] = useState(false);
  const [analysis, setAnalysis] = useState<ImageAnalysisResponse | null>(null);
  const [useDocumentVision, setUseDocumentVision] = useState(false);
  const [useUiVision, setUseUiVision] = useState(false);
  const [useOperatorAssist, setUseOperatorAssist] = useState(false);
  const [operatorContext, setOperatorContext] = useState('');

  const handlePickImage = async () => {
    if (!visionToolsEnabled) {
      Toast.show({
        type: 'info',
        text1: 'Vision tools are off',
        text2: DEFAULT_DISABLED_MESSAGE,
      });
      return;
    }

    const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permission.granted) {
      Toast.show({
        type: 'error',
        text1: 'Permission needed',
        text2: 'Photo library permission is required to pick an image.',
      });
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: false,
      quality: 1,
    });

    if (!result.canceled) {
      setSelectedAsset(result.assets[0]);
      setAnalysis(null);
    }
  };

  const handleAnalyze = async () => {
    if (!visionToolsEnabled) {
      Toast.show({
        type: 'info',
        text1: 'Vision tools are off',
        text2: DEFAULT_DISABLED_MESSAGE,
      });
      return;
    }

    if (!selectedAsset) {
      Toast.show({
        type: 'error',
        text1: 'Pick an image',
        text2: 'Choose an image before analyzing.',
      });
      return;
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('image', {
        uri: selectedAsset.uri,
        name: selectedAsset.fileName || 'mobile-image.jpg',
        type: selectedAsset.mimeType || guessMimeType(selectedAsset.uri),
      } as never);
      formData.append('include_ocr', String(useDocumentVision) as never);
      formData.append('include_ui', String(useUiVision) as never);
      formData.append('include_operator_assist', String(useOperatorAssist) as never);
      if (operatorContext.trim()) {
        formData.append('operator_context', operatorContext.trim() as never);
      }

      const response = await apiClient.post<ImageAnalysisResponse>(
        '/api/image/analyze',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );
      setAnalysis(response.data);
      Toast.show({
        type: 'success',
        text1: 'Analysis ready',
        text2: 'Grounded image analysis completed.',
      });
    } catch (error) {
      Toast.show({
        type: 'error',
        text1: 'Analysis failed',
        text2: getApiErrorMessage(error, 'Could not analyze image'),
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <ScrollView style={styles.container} contentContainerStyle={styles.content}>
      <View style={styles.section}>
        <Text style={styles.helperText}>API: {apiBaseUrl}</Text>
        <Text style={styles.title}>Image Analyzer</Text>
        <Text style={styles.description}>
          This mobile screen is fully wired now, but kept off by default until you opt into mobile vision tools.
        </Text>
      </View>

      <View style={styles.noticeCard}>
        <Text style={styles.noticeTitle}>
          {visionToolsEnabled ? 'Mobile vision is enabled for this app build.' : 'Ready, but disabled by default.'}
        </Text>
        <Text style={styles.noticeBody}>
          {visionToolsEnabled
            ? 'Pick an image and AAIS will return grounded visual labels, palette data, and a compact summary.'
            : DEFAULT_DISABLED_MESSAGE}
        </Text>
      </View>

      <TouchableOpacity
        style={[styles.optionChip, useDocumentVision && styles.optionChipActive]}
        onPress={() => setUseDocumentVision((value) => !value)}
      >
        <Text style={[styles.optionChipText, useDocumentVision && styles.optionChipTextActive]}>
          Document Vision (OCR): {useDocumentVision ? 'On for this request' : 'Off by default'}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.optionChip, useUiVision && styles.optionChipActive]}
        onPress={() => setUseUiVision((value) => !value)}
      >
        <Text style={[styles.optionChipText, useUiVision && styles.optionChipTextActive]}>
          Screenshot / UI Understanding: {useUiVision ? 'On for this request' : 'Off by default'}
        </Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.optionChip, useOperatorAssist && styles.optionChipActive]}
        onPress={() => setUseOperatorAssist((value) => !value)}
      >
        <Text style={[styles.optionChipText, useOperatorAssist && styles.optionChipTextActive]}>
          Screenshot-To-Action: {useOperatorAssist ? 'On for this request' : 'Off by default'}
        </Text>
      </TouchableOpacity>

      {useOperatorAssist ? (
        <View style={styles.contextCard}>
          <Text style={styles.contextTitle}>Operator hint</Text>
          <Text style={styles.contextBody}>
            Tell Jarvis what to look for if you want a stronger workspace match.
          </Text>
          <TextInput
            value={operatorContext}
            onChangeText={setOperatorContext}
            placeholder="Debug the chat route in api.py"
            placeholderTextColor="#98a2b3"
            multiline
            textAlignVertical="top"
            style={styles.contextInput}
          />
        </View>
      ) : null}

      <TouchableOpacity style={styles.primaryButton} onPress={handlePickImage}>
        <Text style={styles.primaryButtonText}>
          {selectedAsset ? 'Choose a Different Image' : 'Pick an Image'}
        </Text>
      </TouchableOpacity>

      {selectedAsset ? (
        <View style={styles.previewCard}>
          <Image source={{ uri: selectedAsset.uri }} style={styles.previewImage} />
          <Text style={styles.previewMeta}>
            {selectedAsset.fileName || 'Selected image'}
          </Text>
        </View>
      ) : (
        <View style={styles.placeholderCard}>
          <Text style={styles.placeholderText}>No image selected yet.</Text>
        </View>
      )}

      <TouchableOpacity
        style={[styles.secondaryButton, (!selectedAsset || loading) && styles.buttonDisabled]}
        onPress={handleAnalyze}
        disabled={!selectedAsset || loading}
      >
        {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.secondaryButtonText}>Analyze Image</Text>}
      </TouchableOpacity>

      {analysis ? (
        <View style={styles.analysisCard}>
          <Text style={styles.analysisTitle}>Grounded Summary</Text>
          <Text style={styles.analysisText}>{analysis.description}</Text>
          <View style={styles.metaRow}>
            <Text style={styles.metaBadge}>{analysis.analysis_method || 'vision-read'}</Text>
            {!!analysis.image_size && (
              <Text style={styles.metaBadge}>
                {analysis.image_size.width}x{analysis.image_size.height} {analysis.image_size.orientation}
              </Text>
            )}
          </View>

          {!!analysis.top_matches?.length && (
            <View style={styles.block}>
              <Text style={styles.blockTitle}>Top Matches</Text>
              <View style={styles.badgeGrid}>
                {analysis.top_matches.map((match) => (
                  <Text key={match.label} style={styles.badge}>
                    {match.label} {Math.round(match.score * 100)}%
                  </Text>
                ))}
              </View>
            </View>
          )}

          {!!analysis.dominant_colors?.length && (
            <View style={styles.block}>
              <Text style={styles.blockTitle}>Dominant Colors</Text>
              <View style={styles.colorGrid}>
                {analysis.dominant_colors.map((color) => (
                  <View key={color.hex} style={styles.colorBadge}>
                    <View style={[styles.swatch, { backgroundColor: color.hex }]} />
                    <Text style={styles.colorText}>
                      {color.hex} {Math.round(color.share * 100)}%
                    </Text>
                  </View>
                ))}
              </View>
            </View>
          )}

          {!!analysis.ocr && (
            <View style={styles.block}>
              <Text style={styles.blockTitle}>Document Vision</Text>
              <Text style={styles.analysisText}>{analysis.ocr.summary}</Text>
              <View style={styles.badgeGrid}>
                <Text style={styles.badge}>{analysis.ocr.status}</Text>
                {!!analysis.ocr.engine && <Text style={styles.badge}>{analysis.ocr.engine}</Text>}
                {!!analysis.ocr.word_count && (
                  <Text style={styles.badge}>{analysis.ocr.word_count} words</Text>
                )}
                {analysis.ocr.average_confidence != null && (
                  <Text style={styles.badge}>
                    {Math.round(analysis.ocr.average_confidence)}% confidence
                  </Text>
                )}
              </View>
              {!!analysis.ocr.text_preview && (
                <View style={styles.ocrPreviewCard}>
                  <Text style={styles.ocrPreviewText}>{analysis.ocr.text_preview}</Text>
                </View>
              )}
            </View>
          )}

          {!!analysis.ui && (
            <View style={styles.block}>
              <Text style={styles.blockTitle}>UI Understanding</Text>
              <Text style={styles.analysisText}>{analysis.ui.summary}</Text>
              <View style={styles.badgeGrid}>
                <Text style={styles.badge}>{analysis.ui.status}</Text>
                {!!analysis.ui.surface_type && <Text style={styles.badge}>{analysis.ui.surface_type}</Text>}
                {!!analysis.ui.platform_hint && <Text style={styles.badge}>{analysis.ui.platform_hint}</Text>}
                {!!analysis.ui.theme && <Text style={styles.badge}>{analysis.ui.theme} theme</Text>}
                {!!analysis.ui.panel_estimate && (
                  <Text style={styles.badge}>{analysis.ui.panel_estimate} regions</Text>
                )}
                {!!analysis.ui.density_label && (
                  <Text style={styles.badge}>{analysis.ui.density_label} density</Text>
                )}
                {!!analysis.ui.code_language && (
                  <Text style={styles.badge}>{analysis.ui.code_language}</Text>
                )}
              </View>
              {!!analysis.ui.layout_clues?.length && (
                <View style={styles.subBlock}>
                  <Text style={styles.subBlockTitle}>Layout clues</Text>
                  <View style={styles.badgeGrid}>
                    {analysis.ui.layout_clues.map((clue) => (
                      <Text key={clue} style={styles.badge}>{clue}</Text>
                    ))}
                  </View>
                </View>
              )}
              {!!analysis.ui.readable_targets?.length && (
                <View style={styles.subBlock}>
                  <Text style={styles.subBlockTitle}>Readable targets</Text>
                  <View style={styles.badgeGrid}>
                    {analysis.ui.readable_targets.map((target) => (
                      <Text key={target} style={styles.badge}>{target}</Text>
                    ))}
                  </View>
                </View>
              )}
            </View>
          )}

          {!!analysis.operator_assist && (
            <View style={styles.block}>
              <Text style={styles.blockTitle}>Screenshot-To-Action</Text>
              {!!analysis.operator_assist.summary && (
                <Text style={styles.analysisText}>{analysis.operator_assist.summary}</Text>
              )}
              <View style={styles.badgeGrid}>
                {!!analysis.operator_assist.surface_type && (
                  <Text style={styles.badge}>{analysis.operator_assist.surface_type}</Text>
                )}
                {!!analysis.operator_assist.code_language && (
                  <Text style={styles.badge}>{analysis.operator_assist.code_language}</Text>
                )}
                {!!analysis.operator_assist.debug_signals?.length && (
                  <Text style={styles.badge}>
                    {analysis.operator_assist.debug_signals.length} debug signals
                  </Text>
                )}
              </View>
              {!!analysis.operator_assist.workspace_query && (
                <View style={styles.subBlock}>
                  <Text style={styles.subBlockTitle}>Workspace query</Text>
                  <Text style={styles.analysisText}>{analysis.operator_assist.workspace_query}</Text>
                </View>
              )}
              {!!analysis.operator_assist.suggested_action && (
                <View style={styles.resultCard}>
                  <Text style={styles.subBlockTitle}>{analysis.operator_assist.suggested_action.label}</Text>
                  {!!analysis.operator_assist.action_reason && (
                    <Text style={styles.analysisText}>{analysis.operator_assist.action_reason}</Text>
                  )}
                  {!!analysis.operator_assist.suggested_action.command_preview && (
                    <Text style={styles.commandPreview}>
                      {analysis.operator_assist.suggested_action.command_preview}
                    </Text>
                  )}
                </View>
              )}
              {!!analysis.operator_assist.debug_signals?.length && (
                <View style={styles.subBlock}>
                  <Text style={styles.subBlockTitle}>Debug signals</Text>
                  <View style={styles.badgeGrid}>
                    {analysis.operator_assist.debug_signals.map((signal) => (
                      <Text key={signal} style={styles.badge}>{signal}</Text>
                    ))}
                  </View>
                </View>
              )}
              {!!analysis.operator_assist.workspace_context?.results?.length && (
                <View style={styles.subBlock}>
                  <Text style={styles.subBlockTitle}>Workspace matches</Text>
                  {analysis.operator_assist.workspace_context.results.map((result) => (
                    <View key={result.relative_path} style={styles.resultCard}>
                      <Text style={styles.resultPath}>{result.relative_path}</Text>
                      {!!result.snippet && <Text style={styles.analysisText}>{result.snippet}</Text>}
                    </View>
                  ))}
                </View>
              )}
              {!!analysis.operator_assist.next_steps?.length && (
                <View style={styles.subBlock}>
                  <Text style={styles.subBlockTitle}>Next steps</Text>
                  {analysis.operator_assist.next_steps.map((step) => (
                    <Text key={step} style={styles.stepText}>• {step}</Text>
                  ))}
                </View>
              )}
            </View>
          )}
        </View>
      ) : null}
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
    backgroundColor: '#e8f4f2',
    borderWidth: 1,
    borderColor: '#c6e7e1',
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
  contextCard: {
    padding: 16,
    borderRadius: 18,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#dde3ea',
    gap: 8,
  },
  contextTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#102132',
  },
  contextBody: {
    fontSize: 13,
    lineHeight: 19,
    color: '#475467',
  },
  contextInput: {
    minHeight: 88,
    paddingHorizontal: 12,
    paddingVertical: 10,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: '#cfd6de',
    backgroundColor: '#f8fafc',
    color: '#102132',
  },
  primaryButton: {
    paddingVertical: 14,
    borderRadius: 16,
    backgroundColor: '#102132',
    alignItems: 'center',
  },
  optionChip: {
    paddingVertical: 12,
    paddingHorizontal: 14,
    borderRadius: 999,
    backgroundColor: '#eef2f6',
    alignSelf: 'flex-start',
  },
  optionChipActive: {
    backgroundColor: '#102132',
  },
  optionChipText: {
    color: '#344054',
    fontWeight: '700',
  },
  optionChipTextActive: {
    color: '#fff',
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '700',
  },
  previewCard: {
    borderRadius: 22,
    overflow: 'hidden',
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#dde3ea',
  },
  previewImage: {
    width: '100%',
    height: 260,
    backgroundColor: '#d0d5dd',
  },
  previewMeta: {
    padding: 12,
    fontSize: 13,
    color: '#475467',
  },
  placeholderCard: {
    borderRadius: 22,
    borderWidth: 1,
    borderColor: '#dde3ea',
    borderStyle: 'dashed',
    padding: 24,
    alignItems: 'center',
    backgroundColor: '#fff',
  },
  placeholderText: {
    color: '#667085',
  },
  secondaryButton: {
    paddingVertical: 14,
    borderRadius: 16,
    backgroundColor: '#0f766e',
    alignItems: 'center',
  },
  secondaryButtonText: {
    color: '#fff',
    fontSize: 15,
    fontWeight: '700',
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  analysisCard: {
    padding: 18,
    borderRadius: 22,
    backgroundColor: '#fff',
    borderWidth: 1,
    borderColor: '#dde3ea',
    gap: 12,
  },
  analysisTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#102132',
  },
  analysisText: {
    fontSize: 15,
    lineHeight: 22,
    color: '#344054',
  },
  metaRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  metaBadge: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    backgroundColor: '#f0f4f8',
    color: '#344054',
    overflow: 'hidden',
  },
  block: {
    gap: 10,
  },
  subBlock: {
    gap: 8,
  },
  subBlockTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#102132',
  },
  blockTitle: {
    fontSize: 15,
    fontWeight: '700',
    color: '#102132',
  },
  badgeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  badge: {
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 999,
    backgroundColor: '#f6f8fb',
    color: '#344054',
    overflow: 'hidden',
  },
  colorGrid: {
    gap: 8,
  },
  colorBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    padding: 10,
    borderRadius: 14,
    backgroundColor: '#f8fafc',
  },
  swatch: {
    width: 18,
    height: 18,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: '#cbd5e1',
  },
  colorText: {
    color: '#344054',
  },
  ocrPreviewCard: {
    padding: 12,
    borderRadius: 14,
    backgroundColor: '#101828',
  },
  ocrPreviewText: {
    color: '#f8fafc',
    lineHeight: 20,
  },
  resultCard: {
    padding: 12,
    borderRadius: 14,
    backgroundColor: '#f8fafc',
    borderWidth: 1,
    borderColor: '#dde3ea',
    gap: 6,
  },
  resultPath: {
    fontSize: 13,
    fontWeight: '700',
    color: '#102132',
  },
  commandPreview: {
    paddingHorizontal: 10,
    paddingVertical: 8,
    borderRadius: 12,
    backgroundColor: '#101828',
    color: '#f8fafc',
    overflow: 'hidden',
  },
  stepText: {
    fontSize: 14,
    lineHeight: 20,
    color: '#344054',
  },
});

export default ImageAnalyzerScreen;
