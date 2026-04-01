import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

const ImageAnalyzerScreen = () => {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Image Analyzer</Text>
      <Text style={styles.description}>Coming soon...</Text>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#333',
  },
  description: {
    fontSize: 14,
    color: '#666',
    marginTop: 8,
  },
});

export default ImageAnalyzerScreen;
