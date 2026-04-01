import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

const SettingsScreen = () => {
  const settings = [
    { title: 'Account', icon: 'account' },
    { title: 'Notifications', icon: 'bell' },
    { title: 'Privacy', icon: 'lock' },
    { title: 'About', icon: 'information' },
    { title: 'Logout', icon: 'logout' },
  ];

  return (
    <ScrollView style={styles.container}>
      {settings.map((setting, index) => (
        <TouchableOpacity key={index} style={styles.settingItem}>
          <Icon name={setting.icon} size={24} color="#667eea" />
          <Text style={styles.settingText}>{setting.title}</Text>
          <Icon name="chevron-right" size={24} color="#ccc" />
        </TouchableOpacity>
      ))}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#fff',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#e0e0e0',
  },
  settingText: {
    flex: 1,
    fontSize: 16,
    color: '#333',
    marginLeft: 16,
  },
});

export default SettingsScreen;
