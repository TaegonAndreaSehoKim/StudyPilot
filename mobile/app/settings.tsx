import { useEffect, useState } from 'react';
import { ScrollView, StyleSheet, Text, TextInput } from 'react-native';

import { api, getAccessToken, getApiBaseUrl, setAccessToken, setApiBaseUrl } from '@/api/client';
import { Button } from '@/components/Button';
import { Card } from '@/components/Card';
import { ErrorState } from '@/components/ErrorState';
import { colors } from '@/constants/colors';

export default function SettingsScreen() {
  const [baseUrl, setBaseUrl] = useState('');
  const [accessToken, setLocalAccessToken] = useState('');
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

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
      setStatus('Saved');
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
      setStatus(`${health.app} backend is ${health.status}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to connect to backend');
    } finally {
      setSaving(false);
    }
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {error ? <ErrorState message={error} /> : null}
      <Card>
        <Text style={styles.label}>API Base URL</Text>
        <TextInput
          value={baseUrl}
          onChangeText={setBaseUrl}
          autoCapitalize="none"
          autoCorrect={false}
          placeholder="http://127.0.0.1:8000"
          style={styles.input}
        />
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
        <Button title={saving ? 'Working...' : 'Save'} disabled={saving} onPress={save} />
        <Button title="Test Connection" variant="secondary" disabled={saving} onPress={testConnection} />
        {status ? <Text style={styles.status}>{status}</Text> : null}
      </Card>
      <Text style={styles.note}>
        iOS simulator usually works with 127.0.0.1. Android emulator often needs 10.0.2.2. Physical devices need your computer's LAN IP.
        The backend access token protects write and AI-generation requests after deployment; it is not an OpenAI API key.
      </Text>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 14,
    padding: 16,
  },
  label: {
    color: colors.text,
    fontWeight: '800',
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
  note: {
    color: colors.textMuted,
    lineHeight: 20,
  },
});
