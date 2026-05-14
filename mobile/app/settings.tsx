import * as Updates from 'expo-updates';
import { useEffect, useState } from 'react';
import { Alert, StyleSheet, Text, TextInput, View } from 'react-native';

import { api, getAccessToken, getApiBaseUrl, setAccessToken, setApiBaseUrl } from '@/api/client';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { ErrorState } from '@/components/ErrorState';
import { ScreenScrollView } from '@/components/Screen';
import { colors } from '@/constants/colors';

const API_PRESETS = [
  { label: 'AWS EC2', value: 'http://3.23.120.213:8000' },
  { label: 'Local iOS', value: 'http://127.0.0.1:8000' },
  { label: 'Android emulator', value: 'http://10.0.2.2:8000' },
];

export default function SettingsScreen() {
  const [baseUrl, setBaseUrl] = useState('');
  const [accessToken, setLocalAccessToken] = useState('');
  const [status, setStatus] = useState<string | null>(null);
  const [updateStatus, setUpdateStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [checkingUpdate, setCheckingUpdate] = useState(false);

  useEffect(() => {
    getApiBaseUrl().then(setBaseUrl);
    getAccessToken().then(setLocalAccessToken);
  }, []);

  async function save() {
    try {
      setSaving(true);
      setError(null);
      await setApiBaseUrl(baseUrl);
      await setAccessToken(accessToken);
      setStatus('Settings saved on this device');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save API base URL');
    } finally {
      setSaving(false);
    }
  }

  async function testConnection() {
    try {
      setSaving(true);
      setError(null);
      await setApiBaseUrl(baseUrl);
      await setAccessToken(accessToken);
      const health = await api.health();
      setStatus(`${health.app} backend is ${health.status} at ${baseUrl.trim()}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to connect to backend');
    } finally {
      setSaving(false);
    }
  }

  async function checkForUpdate() {
    try {
      setCheckingUpdate(true);
      setError(null);
      setUpdateStatus(null);

      if (!Updates.isEnabled) {
        setUpdateStatus('EAS Update checks are not enabled in this runtime. In Expo Go, reopen the project after publishing a preview update.');
        return;
      }

      const update = await Updates.checkForUpdateAsync();
      if (!update.isAvailable) {
        setUpdateStatus('No newer EAS update is available for this runtime.');
        return;
      }

      const fetched = await Updates.fetchUpdateAsync();
      if (!fetched.isNew) {
        setUpdateStatus('The latest compatible update is already on this device.');
        return;
      }

      Alert.alert(
        'Update downloaded',
        'Reload StudyPilot now to apply the downloaded update?',
        [
          { text: 'Later', style: 'cancel' },
          { text: 'Reload', onPress: () => { void Updates.reloadAsync(); } },
        ],
      );
      setUpdateStatus('Update downloaded. Reload the app to apply it.');
    } catch (err) {
      setUpdateStatus(
        'Manual update checks are unavailable in Expo Go or local development. Reopen the project after publishing a preview update.',
      );
      if (err instanceof Error && !err.message.toLowerCase().includes('expo go')) {
        setError(err.message);
      }
    } finally {
      setCheckingUpdate(false);
    }
  }

  return (
    <ScreenScrollView contentContainerStyle={styles.container}>
      {error ? <ErrorState message={error} /> : null}
      <Card>
        <View style={styles.header}>
          <Text style={styles.title}>Backend Connection</Text>
          <Text style={styles.badge}>{accessToken.trim() ? 'Token saved' : 'Token missing'}</Text>
        </View>
        <Text style={styles.noteSmall}>
          Pick a preset or enter a custom backend URL. The AWS preset points to the current StudyPilot EC2 Elastic IP.
        </Text>
        <View style={styles.presetGrid}>
          {API_PRESETS.map((preset) => (
            <Button
              key={preset.value}
              title={preset.label}
              variant={baseUrl.trim() === preset.value ? 'primary' : 'secondary'}
              disabled={saving}
              onPress={() => {
                setBaseUrl(preset.value);
                setStatus(null);
                setError(null);
              }}
            />
          ))}
        </View>
        <Text style={styles.label}>API Base URL</Text>
        <TextInput
          value={baseUrl}
          onChangeText={setBaseUrl}
          autoCapitalize="none"
          autoCorrect={false}
          placeholder="http://127.0.0.1:8000"
          style={styles.input}
        />
        <Text style={styles.helper}>Current target: {baseUrl.trim() || 'Not set'}</Text>
        <Text style={styles.label}>Backend Access Token</Text>
        <TextInput
          value={accessToken}
          onChangeText={setLocalAccessToken}
          autoCapitalize="none"
          autoCorrect={false}
          placeholder="Required when backend BACKEND_ACCESS_TOKEN is set"
          secureTextEntry
          style={styles.input}
        />
        <Text style={styles.helper}>
          The token is stored only on this device and is sent as X-StudyPilot-Key for write and generation requests.
        </Text>
        <View style={styles.actions}>
          <Button title={saving ? 'Working...' : 'Save'} disabled={saving} onPress={save} />
          <Button title="Save & Test Connection" variant="secondary" disabled={saving} onPress={testConnection} />
        </View>
        {status ? <Text style={styles.status}>{status}</Text> : null}
      </Card>

      <Card>
        <View style={styles.header}>
          <Text style={styles.title}>App Update</Text>
          <Text style={styles.badge}>{Updates.isEnabled ? 'Updates enabled' : 'Expo Go / Dev'}</Text>
        </View>
        <Text style={styles.noteSmall}>
          Use this to confirm which EAS update is running. Expo Go usually applies preview updates when you reopen the project.
        </Text>
        <View style={styles.infoRows}>
          <InfoRow label="Channel" value={Updates.channel || 'Expo Go compatible update'} />
          <InfoRow label="Runtime" value={Updates.runtimeVersion || 'Not reported'} />
          <InfoRow label="Update ID" value={Updates.updateId ? Updates.updateId.slice(0, 8) : 'Local or embedded'} />
          <InfoRow label="Created" value={Updates.createdAt ? Updates.createdAt.toLocaleString() : 'Not reported'} />
        </View>
        <Button
          title={checkingUpdate ? 'Checking...' : 'Check for EAS Update'}
          variant="secondary"
          disabled={checkingUpdate}
          onPress={checkForUpdate}
        />
        {updateStatus ? <Text style={styles.helper}>{updateStatus}</Text> : null}
      </Card>

      <Text style={styles.note}>
        Expo Go can use the AWS EC2 preset over HTTP for MVP testing. Standalone iOS or App Store builds should use an HTTPS backend.
        The backend access token is not an OpenAI API key.
      </Text>
    </ScreenScrollView>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text style={styles.infoValue} numberOfLines={2}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 14,
    maxWidth: 720,
  },
  label: {
    color: colors.text,
    fontWeight: '800',
  },
  header: {
    alignItems: 'flex-start',
    flexDirection: 'row',
    gap: 10,
    justifyContent: 'space-between',
  },
  title: {
    color: colors.text,
    fontSize: 18,
    fontWeight: '900',
  },
  badge: {
    backgroundColor: colors.infoSurface,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    color: colors.text,
    fontSize: 12,
    fontWeight: '800',
    overflow: 'hidden',
    paddingHorizontal: 8,
    paddingVertical: 4,
  },
  presetGrid: {
    gap: 8,
  },
  actions: {
    gap: 8,
  },
  infoRows: {
    gap: 8,
  },
  infoRow: {
    alignItems: 'flex-start',
    borderBottomColor: colors.border,
    borderBottomWidth: 1,
    gap: 4,
    paddingBottom: 8,
  },
  infoLabel: {
    color: colors.textMuted,
    fontSize: 12,
    fontWeight: '800',
    textTransform: 'uppercase',
  },
  infoValue: {
    color: colors.text,
    fontWeight: '700',
    lineHeight: 20,
  },
  input: {
    backgroundColor: colors.surface,
    borderColor: colors.border,
    borderRadius: 8,
    borderWidth: 1,
    color: colors.text,
    fontSize: 16,
    minHeight: 46,
    paddingHorizontal: 12,
  },
  status: {
    color: colors.success,
    fontWeight: '800',
  },
  helper: {
    color: colors.textMuted,
    fontSize: 13,
    lineHeight: 18,
  },
  noteSmall: {
    color: colors.textMuted,
    lineHeight: 20,
  },
  note: {
    color: colors.textMuted,
    lineHeight: 20,
  },
});
