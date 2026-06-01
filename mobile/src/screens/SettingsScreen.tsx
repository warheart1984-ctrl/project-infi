import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { MaterialCommunityIcons as Icon } from '@expo/vector-icons';

type IconName = React.ComponentProps<typeof Icon>['name'];

const SettingsScreen = () => {
  const settings = [
    { title: 'Account', icon: 'account' as IconName },
    { title: 'Notifications', icon: 'bell' as IconName },
    { title: 'Privacy', icon: 'lock' as IconName },
    { title: 'About', icon: 'information' as IconName },
    { title: 'Logout', icon: 'logout' as IconName },
  ] as const;

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
