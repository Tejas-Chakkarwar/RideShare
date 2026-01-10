# SJSU RideShare Development Guide
## Section 14: React Native Mobile App

**Version:** 2.0 (Updated for Sections 1-13)
**Duration:** Week 14-17 (3-4 weeks)
**Focus:** Complete Mobile App with All Backend Features

---

# TABLE OF CONTENTS

1. [Overview & Setup](#overview)
2. [Project Structure](#structure)
3. [Navigation & Authentication](#navigation)
4. [User Profile & Verification](#profile)
5. [Ride Creation & Search](#rides)
6. [Booking & Payments](#booking)
7. [Real-Time Tracking](#tracking)
8. [Ratings & Reviews](#ratings)
9. [Advanced Features](#advanced)
10. [Push Notifications](#notifications)
11. [SJSU-Specific Features](#sjsu)
12. [Testing & Deployment](#deployment)

---

<a name="overview"></a>
# PART 1: OVERVIEW & SETUP

## What We're Building

A **feature-complete React Native mobile app** that connects to all 5 backend services:

✅ **Authentication & Profiles** (User Service)
- Login/Register
- Email/Phone/SJSU verification
- Profile editing with photo upload
- Password management

✅ **Ride Management** (Ride Service)
- Create rides with Google Maps
- Search rides with advanced filters
- Saved locations (Home, Work, SJSU)
- Ride templates
- SJSU campus location picker

✅ **Booking System** (Booking Service)
- Book rides with seat selection
- Approve/reject bookings (drivers)
- Ride history with PDF receipts
- Driver dashboard with earnings

✅ **Payments** (Booking Service + Stripe)
- Add payment methods
- Pay for rides
- View payment history
- Driver payout tracking

✅ **Real-Time Tracking** (Tracking Service)
- Live location sharing
- Trip progress
- ETA updates
- Safety features (share trip, emergency contacts)

✅ **Ratings & Reviews** (Booking Service)
- Rate drivers and passengers
- View ratings history
- User badges

✅ **Notifications** (Notification Service + Firebase)
- Push notifications
- In-app notifications
- Email integration

---

## Technology Stack

```json
{
  "framework": "React Native 0.73+",
  "navigation": "@react-navigation/native 6.x",
  "state_management": "Redux Toolkit + RTK Query",
  "maps": "react-native-maps",
  "location": "@react-native-community/geolocation",
  "payments": "@stripe/stripe-react-native",
  "notifications": "@react-native-firebase/messaging",
  "realtime": "socket.io-client",
  "forms": "react-hook-form + yup",
  "ui": "react-native-paper (Material Design)",
  "images": "react-native-image-picker",
  "pdf": "react-native-pdf",
  "icons": "@expo/vector-icons"
}
```

---

## Project Initialization

```bash
# Create React Native project
npx react-native@latest init SJSURideShare --template react-native-template-typescript

cd SJSURideShare

# Install core dependencies
npm install @react-navigation/native @react-navigation/stack @react-navigation/bottom-tabs
npm install react-native-screens react-native-safe-area-context
npm install @reduxjs/toolkit react-redux
npm install axios

# Install feature dependencies
npm install react-native-maps
npm install @react-native-community/geolocation
npm install @stripe/stripe-react-native
npm install @react-native-firebase/app @react-native-firebase/messaging
npm install socket.io-client
npm install react-hook-form yup @hookform/resolvers
npm install react-native-paper
npm install react-native-image-picker
npm install react-native-pdf
npm install @expo/vector-icons
npm install react-native-vector-icons

# Install dev dependencies
npm install --save-dev @types/react @types/react-native
npm install --save-dev eslint prettier

# iOS setup (Mac only)
cd ios && pod install && cd ..
```

---

<a name="structure"></a>
# PART 2: PROJECT STRUCTURE

```
SJSURideShare/
├── src/
│   ├── api/                    # API client & endpoints
│   │   ├── client.ts           # Axios instance with auth
│   │   ├── auth.ts             # Auth endpoints
│   │   ├── users.ts            # User endpoints
│   │   ├── rides.ts            # Ride endpoints
│   │   ├── bookings.ts         # Booking endpoints
│   │   ├── payments.ts         # Payment endpoints
│   │   ├── tracking.ts         # Tracking endpoints
│   │   ├── ratings.ts          # Rating endpoints
│   │   └── notifications.ts    # Notification endpoints
│   │
│   ├── components/             # Reusable components
│   │   ├── common/
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Card.tsx
│   │   │   └── LoadingSpinner.tsx
│   │   ├── ride/
│   │   │   ├── RideCard.tsx
│   │   │   ├── RideMap.tsx
│   │   │   └── RideFilters.tsx
│   │   ├── booking/
│   │   │   ├── BookingCard.tsx
│   │   │   └── SeatSelector.tsx
│   │   ├── profile/
│   │   │   ├── ProfileHeader.tsx
│   │   │   ├── RatingStars.tsx
│   │   │   └── BadgeList.tsx
│   │   └── map/
│   │       ├── MapView.tsx
│   │       ├── LocationPicker.tsx
│   │       └── RoutePolyline.tsx
│   │
│   ├── screens/                # App screens
│   │   ├── auth/
│   │   │   ├── LoginScreen.tsx
│   │   │   ├── RegisterScreen.tsx
│   │   │   └── ForgotPasswordScreen.tsx
│   │   ├── profile/
│   │   │   ├── ProfileScreen.tsx
│   │   │   ├── EditProfileScreen.tsx
│   │   │   ├── VerificationScreen.tsx
│   │   │   └── SavedLocationsScreen.tsx
│   │   ├── rides/
│   │   │   ├── RideSearchScreen.tsx
│   │   │   ├── CreateRideScreen.tsx
│   │   │   ├── RideDetailsScreen.tsx
│   │   │   ├── MyRidesScreen.tsx
│   │   │   └── RideTemplatesScreen.tsx
│   │   ├── bookings/
│   │   │   ├── BookRideScreen.tsx
│   │   │   ├── MyBookingsScreen.tsx
│   │   │   ├── BookingDetailsScreen.tsx
│   │   │   └── DriverRequestsScreen.tsx
│   │   ├── tracking/
│   │   │   ├── LiveTrackingScreen.tsx
│   │   │   └── ShareTripScreen.tsx
│   │   ├── ratings/
│   │   │   ├── RateRideScreen.tsx
│   │   │   └── RatingsHistoryScreen.tsx
│   │   ├── payments/
│   │   │   ├── PaymentMethodsScreen.tsx
│   │   │   ├── AddPaymentScreen.tsx
│   │   │   └── PaymentHistoryScreen.tsx
│   │   ├── dashboard/
│   │   │   ├── HomeScreen.tsx
│   │   │   └── DriverDashboardScreen.tsx
│   │   └── sjsu/
│   │       ├── CampusLocationsScreen.tsx
│   │       └── EventRidesScreen.tsx
│   │
│   ├── navigation/             # Navigation setup
│   │   ├── AppNavigator.tsx
│   │   ├── AuthNavigator.tsx
│   │   └── MainNavigator.tsx
│   │
│   ├── store/                  # Redux store
│   │   ├── index.ts
│   │   ├── slices/
│   │   │   ├── authSlice.ts
│   │   │   ├── userSlice.ts
│   │   │   ├── rideSlice.ts
│   │   │   └── notificationSlice.ts
│   │   └── api/
│   │       └── apiSlice.ts     # RTK Query
│   │
│   ├── services/               # Business logic
│   │   ├── websocket.ts        # Socket.io client
│   │   ├── geolocation.ts      # Location services
│   │   ├── notifications.ts    # Push notifications
│   │   └── storage.ts          # AsyncStorage wrapper
│   │
│   ├── utils/                  # Utilities
│   │   ├── validators.ts       # Form validation
│   │   ├── formatters.ts       # Date, currency formatters
│   │   ├── constants.ts        # App constants
│   │   └── permissions.ts      # Permission handling
│   │
│   ├── types/                  # TypeScript types
│   │   ├── auth.ts
│   │   ├── user.ts
│   │   ├── ride.ts
│   │   ├── booking.ts
│   │   └── api.ts
│   │
│   └── theme/                  # Theming
│       ├── colors.ts
│       ├── typography.ts
│       └── spacing.ts
│
├── android/                    # Android native code
├── ios/                        # iOS native code
├── App.tsx                     # Root component
└── package.json
```

---

<a name="navigation"></a>
# PART 3: NAVIGATION & AUTHENTICATION

## API Client Setup

**File:** `src/api/client.ts`

```typescript
import axios, { AxiosInstance, AxiosRequestConfig } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const BASE_URL = __DEV__
  ? 'http://localhost:8001'  // Development
  : 'https://api.sjsurideshare.com';  // Production

class APIClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: BASE_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor - add auth token
    this.client.interceptors.request.use(
      async (config) => {
        const token = await AsyncStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor - handle errors
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          // Token expired, logout user
          await AsyncStorage.removeItem('access_token');
          // Navigate to login (handled by navigation)
        }
        return Promise.reject(error);
      }
    );
  }

  get<T>(url: string, config?: AxiosRequestConfig) {
    return this.client.get<T>(url, config);
  }

  post<T>(url: string, data?: any, config?: AxiosRequestConfig) {
    return this.client.post<T>(url, data, config);
  }

  put<T>(url: string, data?: any, config?: AxiosRequestConfig) {
    return this.client.put<T>(url, data, config);
  }

  delete<T>(url: string, config?: AxiosRequestConfig) {
    return this.client.delete<T>(url, config);
  }

  // Service-specific base URLs
  getUserServiceURL() {
    return __DEV__ ? 'http://localhost:8001' : 'https://api.sjsurideshare.com';
  }

  getRideServiceURL() {
    return __DEV__ ? 'http://localhost:8002' : 'https://api.sjsurideshare.com';
  }

  getBookingServiceURL() {
    return __DEV__ ? 'http://localhost:8003' : 'https://api.sjsurideshare.com';
  }

  getTrackingServiceURL() {
    return __DEV__ ? 'http://localhost:8005' : 'https://api.sjsurideshare.com';
  }
}

export const apiClient = new APIClient();
```

## Auth API

**File:** `src/api/auth.ts`

```typescript
import { apiClient } from './client';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    full_name: string;
    email_verified: boolean;
    phone_verified: boolean;
    sjsu_email_verified: boolean;
  };
}

export const authAPI = {
  async login(data: LoginRequest): Promise<AuthResponse> {
    const formData = new FormData();
    formData.append('username', data.email);
    formData.append('password', data.password);

    const response = await apiClient.post<{ access_token: string; token_type: string }>(
      '/api/v1/auth/login/access-token',
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );

    // Save token
    await AsyncStorage.setItem('access_token', response.data.access_token);

    // Get user profile
    const userResponse = await apiClient.get('/api/v1/users/me');

    return {
      ...response.data,
      user: userResponse.data,
    };
  },

  async register(data: RegisterRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/api/v1/auth/register', data);

    // Save token
    await AsyncStorage.setItem('access_token', response.data.access_token);

    return response.data;
  },

  async logout(): Promise<void> {
    await AsyncStorage.removeItem('access_token');
  },

  async forgotPassword(email: string): Promise<void> {
    await apiClient.post('/api/v1/auth/forgot-password', { email });
  },

  async checkAuth(): Promise<boolean> {
    const token = await AsyncStorage.getItem('access_token');
    return !!token;
  },
};
```

## Redux Store Setup

**File:** `src/store/slices/authSlice.ts`

```typescript
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { authAPI, LoginRequest, RegisterRequest, AuthResponse } from '../../api/auth';

interface AuthState {
  user: AuthResponse['user'] | null;
  token: string | null;
  loading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  token: null,
  loading: false,
  error: null,
};

export const login = createAsyncThunk(
  'auth/login',
  async (credentials: LoginRequest, { rejectWithValue }) => {
    try {
      const response = await authAPI.login(credentials);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Login failed');
    }
  }
);

export const register = createAsyncThunk(
  'auth/register',
  async (data: RegisterRequest, { rejectWithValue }) => {
    try {
      const response = await authAPI.register(data);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Registration failed');
    }
  }
);

export const logout = createAsyncThunk('auth/logout', async () => {
  await authAPI.logout();
});

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setUser: (state, action: PayloadAction<AuthResponse['user']>) => {
      state.user = action.payload;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.token = action.payload.access_token;
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Register
      .addCase(register.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state, action) => {
        state.loading = false;
        state.user = action.payload.user;
        state.token = action.payload.access_token;
      })
      .addCase(register.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Logout
      .addCase(logout.fulfilled, (state) => {
        state.user = null;
        state.token = null;
      });
  },
});

export const { setUser, clearError } = authSlice.actions;
export default authSlice.reducer;
```

## Login Screen

**File:** `src/screens/auth/LoginScreen.tsx`

```typescript
import React, { useState } from 'react';
import {
  View,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  Alert,
} from 'react-native';
import { TextInput, Button, Text, HelperText } from 'react-native-paper';
import { useDispatch, useSelector } from 'react-redux';
import { useForm, Controller } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { login } from '../../store/slices/authSlice';
import type { RootState, AppDispatch } from '../../store';

const schema = yup.object({
  email: yup.string().email('Invalid email').required('Email is required'),
  password: yup.string().min(8, 'Password must be at least 8 characters').required('Password is required'),
});

type LoginFormData = yup.InferType<typeof schema>;

export const LoginScreen = ({ navigation }: any) => {
  const dispatch = useDispatch<AppDispatch>();
  const { loading, error } = useSelector((state: RootState) => state.auth);

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: yupResolver(schema),
  });

  const onSubmit = async (data: LoginFormData) => {
    const result = await dispatch(login(data));

    if (login.fulfilled.match(result)) {
      // Navigation handled by AppNavigator
    } else {
      Alert.alert('Login Failed', error || 'Please try again');
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView contentContainerStyle={styles.scrollView}>
        <View style={styles.content}>
          <Text variant="displaySmall" style={styles.title}>
            SJSU RideShare
          </Text>
          <Text variant="bodyLarge" style={styles.subtitle}>
            Login to your account
          </Text>

          <Controller
            control={control}
            name="email"
            render={({ field: { onChange, value } }) => (
              <>
                <TextInput
                  label="Email"
                  value={value}
                  onChangeText={onChange}
                  mode="outlined"
                  autoCapitalize="none"
                  keyboardType="email-address"
                  style={styles.input}
                  error={!!errors.email}
                />
                {errors.email && (
                  <HelperText type="error">{errors.email.message}</HelperText>
                )}
              </>
            )}
          />

          <Controller
            control={control}
            name="password"
            render={({ field: { onChange, value } }) => (
              <>
                <TextInput
                  label="Password"
                  value={value}
                  onChangeText={onChange}
                  mode="outlined"
                  secureTextEntry
                  style={styles.input}
                  error={!!errors.password}
                />
                {errors.password && (
                  <HelperText type="error">{errors.password.message}</HelperText>
                )}
              </>
            )}
          />

          <Button
            mode="contained"
            onPress={handleSubmit(onSubmit)}
            loading={loading}
            disabled={loading}
            style={styles.button}
          >
            Login
          </Button>

          <Button
            mode="text"
            onPress={() => navigation.navigate('ForgotPassword')}
          >
            Forgot Password?
          </Button>

          <Button
            mode="text"
            onPress={() => navigation.navigate('Register')}
          >
            Don't have an account? Register
          </Button>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  scrollView: {
    flexGrow: 1,
  },
  content: {
    flex: 1,
    padding: 20,
    justifyContent: 'center',
  },
  title: {
    textAlign: 'center',
    marginBottom: 10,
    fontWeight: 'bold',
  },
  subtitle: {
    textAlign: 'center',
    marginBottom: 30,
    color: '#666',
  },
  input: {
    marginBottom: 10,
  },
  button: {
    marginTop: 20,
    marginBottom: 10,
  },
});
```

## App Navigator

**File:** `src/navigation/AppNavigator.tsx`

```typescript
import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { useSelector } from 'react-redux';
import { AuthNavigator } from './AuthNavigator';
import { MainNavigator } from './MainNavigator';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { authAPI } from '../api/auth';
import type { RootState } from '../store';

const Stack = createStackNavigator();

export const AppNavigator = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = async () => {
    const hasToken = await authAPI.checkAuth();
    setIsAuthenticated(hasToken);
    setIsLoading(false);
  };

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {user || isAuthenticated ? (
          <Stack.Screen name="Main" component={MainNavigator} />
        ) : (
          <Stack.Screen name="Auth" component={AuthNavigator} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
};
```

---

<a name="profile"></a>
# PART 4: USER PROFILE & VERIFICATION

## Profile Screen

**File:** `src/screens/profile/ProfileScreen.tsx`

```typescript
import React, { useEffect, useState } from 'react';
import { View, StyleSheet, ScrollView, Image, TouchableOpacity, Alert } from 'react-native';
import { Text, Button, Card, Chip, Divider, List } from 'react-native-paper';
import { useSelector } from 'react-redux';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { userAPI } from '../../api/users';
import type { RootState } from '../../store';

export const ProfileScreen = ({ navigation }: any) => {
  const { user } = useSelector((state: RootState) => state.auth);
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchProfile();
  }, []);

  const fetchProfile = async () => {
    try {
      const data = await userAPI.getProfile();
      setProfile(data);
    } catch (error) {
      Alert.alert('Error', 'Failed to load profile');
    } finally {
      setLoading(false);
    }
  };

  if (loading || !profile) {
    return <View style={styles.loading}><Text>Loading...</Text></View>;
  }

  return (
    <ScrollView style={styles.container}>
      {/* Profile Header */}
      <Card style={styles.headerCard}>
        <Card.Content style={styles.headerContent}>
          <TouchableOpacity onPress={() => navigation.navigate('EditProfile')}>
            <Image
              source={
                profile.profile_photo_url
                  ? { uri: profile.profile_photo_url }
                  : require('../../assets/default-avatar.png')
              }
              style={styles.avatar}
            />
            <View style={styles.editIconContainer}>
              <Icon name="camera" size={20} color="#fff" />
            </View>
          </TouchableOpacity>

          <Text variant="headlineSmall" style={styles.name}>
            {profile.full_name}
          </Text>
          <Text variant="bodyMedium" style={styles.email}>
            {profile.email}
          </Text>

          {/* Verification Badges */}
          <View style={styles.badgesContainer}>
            {profile.badges.map((badge: string) => (
              <Chip
                key={badge}
                icon={getBadgeIcon(badge)}
                style={styles.badge}
                textStyle={styles.badgeText}
              >
                {formatBadgeName(badge)}
              </Chip>
            ))}
          </View>

          {/* Ratings */}
          <View style={styles.ratingsContainer}>
            <View style={styles.ratingBox}>
              <Icon name="star" size={24} color="#FFD700" />
              <Text variant="titleMedium">{profile.average_rating_as_driver.toFixed(1)}</Text>
              <Text variant="bodySmall">Driver Rating</Text>
            </View>
            <View style={styles.ratingBox}>
              <Icon name="star" size={24} color="#FFD700" />
              <Text variant="titleMedium">{profile.average_rating_as_passenger.toFixed(1)}</Text>
              <Text variant="bodySmall">Passenger Rating</Text>
            </View>
          </View>

          <View style={styles.statsContainer}>
            <View style={styles.stat}>
              <Text variant="titleLarge">{profile.total_rides_as_driver}</Text>
              <Text variant="bodySmall">Rides as Driver</Text>
            </View>
            <View style={styles.stat}>
              <Text variant="titleLarge">{profile.total_rides_as_passenger}</Text>
              <Text variant="bodySmall">Rides as Passenger</Text>
            </View>
          </View>
        </Card.Content>
      </Card>

      {/* Verification Status */}
      <Card style={styles.card}>
        <Card.Title title="Verification Status" />
        <Card.Content>
          <List.Item
            title="Email Verification"
            left={() => <Icon name="email" size={24} />}
            right={() =>
              profile.email_verified ? (
                <Icon name="check-circle" size={24} color="green" />
              ) : (
                <Button onPress={() => navigation.navigate('Verification', { type: 'email' })}>
                  Verify
                </Button>
              )
            }
          />
          <Divider />
          <List.Item
            title="Phone Verification"
            left={() => <Icon name="phone" size={24} />}
            right={() =>
              profile.phone_verified ? (
                <Icon name="check-circle" size={24} color="green" />
              ) : (
                <Button onPress={() => navigation.navigate('Verification', { type: 'phone' })}>
                  Verify
                </Button>
              )
            }
          />
          <Divider />
          <List.Item
            title="SJSU Email Verification"
            left={() => <Icon name="school" size={24} />}
            right={() =>
              profile.sjsu_email_verified ? (
                <Icon name="check-circle" size={24} color="green" />
              ) : (
                <Button onPress={() => navigation.navigate('Verification', { type: 'sjsu' })}>
                  Verify
                </Button>
              )
            }
          />
        </Card.Content>
      </Card>

      {/* Menu Options */}
      <Card style={styles.card}>
        <List.Item
          title="Edit Profile"
          left={() => <Icon name="account-edit" size={24} />}
          right={() => <Icon name="chevron-right" size={24} />}
          onPress={() => navigation.navigate('EditProfile')}
        />
        <Divider />
        <List.Item
          title="Saved Locations"
          left={() => <Icon name="map-marker" size={24} />}
          right={() => <Icon name="chevron-right" size={24} />}
          onPress={() => navigation.navigate('SavedLocations')}
        />
        <Divider />
        <List.Item
          title="Payment Methods"
          left={() => <Icon name="credit-card" size={24} />}
          right={() => <Icon name="chevron-right" size={24} />}
          onPress={() => navigation.navigate('PaymentMethods')}
        />
        <Divider />
        <List.Item
          title="Change Password"
          left={() => <Icon name="lock" size={24} />}
          right={() => <Icon name="chevron-right" size={24} />}
          onPress={() => navigation.navigate('ChangePassword')}
        />
        <Divider />
        <List.Item
          title="Emergency Contacts"
          left={() => <Icon name="shield-account" size={24} />}
          right={() => <Icon name="chevron-right" size={24} />}
          onPress={() => navigation.navigate('EmergencyContacts')}
        />
      </Card>

      {/* Driver Section (if applicable) */}
      {profile.is_driver && (
        <Card style={styles.card}>
          <Card.Title title="Driver" />
          <Card.Content>
            <List.Item
              title="Driver Dashboard"
              description="View earnings and statistics"
              left={() => <Icon name="chart-line" size={24} />}
              right={() => <Icon name="chevron-right" size={24} />}
              onPress={() => navigation.navigate('DriverDashboard')}
            />
          </Card.Content>
        </Card>
      )}

      <Button
        mode="outlined"
        onPress={() => {/* Logout logic */}}
        style={styles.logoutButton}
      >
        Logout
      </Button>
    </ScrollView>
  );
};

const getBadgeIcon = (badge: string) => {
  const icons: Record<string, string> = {
    sjsu_verified: 'school',
    phone_verified: 'phone-check',
    email_verified: 'email-check',
    top_rated_driver: 'star',
    '100_rides': 'car',
  };
  return icons[badge] || 'badge-account';
};

const formatBadgeName = (badge: string) => {
  const names: Record<string, string> = {
    sjsu_verified: 'SJSU Verified',
    phone_verified: 'Phone Verified',
    email_verified: 'Email Verified',
    top_rated_driver: 'Top Rated',
    '100_rides': '100 Rides',
  };
  return names[badge] || badge;
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loading: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  headerCard: {
    margin: 16,
  },
  headerContent: {
    alignItems: 'center',
    paddingVertical: 20,
  },
  avatar: {
    width: 100,
    height: 100,
    borderRadius: 50,
  },
  editIconContainer: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    backgroundColor: '#6200ee',
    borderRadius: 15,
    padding: 5,
  },
  name: {
    marginTop: 15,
    fontWeight: 'bold',
  },
  email: {
    color: '#666',
    marginTop: 5,
  },
  badgesContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'center',
    marginTop: 15,
  },
  badge: {
    margin: 5,
  },
  badgeText: {
    fontSize: 12,
  },
  ratingsContainer: {
    flexDirection: 'row',
    marginTop: 20,
    gap: 20,
  },
  ratingBox: {
    alignItems: 'center',
  },
  statsContainer: {
    flexDirection: 'row',
    marginTop: 20,
    gap: 40,
  },
  stat: {
    alignItems: 'center',
  },
  card: {
    margin: 16,
    marginTop: 0,
  },
  logoutButton: {
    margin: 16,
    marginBottom: 32,
  },
});
```

## Phone Verification Screen

**File:** `src/screens/profile/VerificationScreen.tsx`

```typescript
import React, { useState } from 'react';
import { View, StyleSheet, Alert } from 'react-native';
import { Text, TextInput, Button, HelperText } from 'react-native-paper';
import { userAPI } from '../../api/users';

export const VerificationScreen = ({ route, navigation }: any) => {
  const { type } = route.params; // 'email', 'phone', or 'sjsu'
  const [step, setStep] = useState<'input' | 'verify'>('input');
  const [value, setValue] = useState('');
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSendCode = async () => {
    setLoading(true);
    try {
      if (type === 'phone') {
        await userAPI.sendPhoneVerification(value);
      } else if (type === 'email') {
        await userAPI.sendEmailVerification();
      } else if (type === 'sjsu') {
        await userAPI.sendSJSUEmailVerification(value);
      }
      setStep('verify');
      Alert.alert('Success', 'Verification code sent!');
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Failed to send code');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCode = async () => {
    setLoading(true);
    try {
      if (type === 'phone') {
        await userAPI.verifyPhone(code);
      } else if (type === 'email') {
        await userAPI.verifyEmail(code);
      } else if (type === 'sjsu') {
        await userAPI.verifySJSUEmail(code);
      }
      Alert.alert('Success', 'Verification complete!');
      navigation.goBack();
    } catch (error: any) {
      Alert.alert('Error', error.response?.data?.detail || 'Invalid code');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <Text variant="headlineSmall" style={styles.title}>
        {type === 'phone' && 'Phone Verification'}
        {type === 'email' && 'Email Verification'}
        {type === 'sjsu' && 'SJSU Email Verification'}
      </Text>

      {step === 'input' ? (
        <>
          <Text variant="bodyMedium" style={styles.description}>
            {type === 'phone' && 'Enter your phone number to receive a verification code'}
            {type === 'email' && 'A verification code will be sent to your registered email'}
            {type === 'sjsu' && 'Enter your @sjsu.edu email address'}
          </Text>

          {type !== 'email' && (
            <TextInput
              label={type === 'phone' ? 'Phone Number' : 'SJSU Email'}
              value={value}
              onChangeText={setValue}
              mode="outlined"
              keyboardType={type === 'phone' ? 'phone-pad' : 'email-address'}
              autoCapitalize="none"
              style={styles.input}
            />
          )}

          <Button
            mode="contained"
            onPress={handleSendCode}
            loading={loading}
            disabled={loading || (type !== 'email' && !value)}
            style={styles.button}
          >
            Send Verification Code
          </Button>
        </>
      ) : (
        <>
          <Text variant="bodyMedium" style={styles.description}>
            Enter the 6-digit code sent to {type === 'phone' ? value : 'your email'}
          </Text>

          <TextInput
            label="Verification Code"
            value={code}
            onChangeText={setCode}
            mode="outlined"
            keyboardType="number-pad"
            maxLength={6}
            style={styles.input}
          />

          <Button
            mode="contained"
            onPress={handleVerifyCode}
            loading={loading}
            disabled={loading || code.length !== 6}
            style={styles.button}
          >
            Verify
          </Button>

          <Button mode="text" onPress={() => setStep('input')}>
            Resend Code
          </Button>
        </>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    backgroundColor: '#fff',
  },
  title: {
    marginBottom: 20,
    fontWeight: 'bold',
  },
  description: {
    marginBottom: 20,
    color: '#666',
  },
  input: {
    marginBottom: 20,
  },
  button: {
    marginBottom: 10,
  },
});
```

---

*[Due to length constraints, I'll continue with remaining sections in a structured format]*

---

<a name="rides"></a>
# PART 5: RIDE CREATION & SEARCH

## Key Components:
- **CreateRideScreen**: Form with Google Maps location picker
- **RideSearchScreen**: Search with filters (price, rating, gender, amenities)
- **RideCard**: Display ride with driver info, ratings, badges
- **LocationPicker**: Google Maps autocomplete + campus locations
- **RideFilters**: Advanced filter modal

## Features:
- ✅ Google Maps integration
- ✅ SJSU campus location quick select
- ✅ Saved locations integration
- ✅ Ride templates (one-click create)
- ✅ Advanced search filters
- ✅ Real-time seat availability

---

<a name="booking"></a>
# PART 6: BOOKING & PAYMENTS

## Stripe Integration

```typescript
import { useStripe } from '@stripe/stripe-react-native';

export const BookRideScreen = ({ route }: any) => {
  const { ride } = route.params;
  const { confirmPayment } = useStripe();

  const handleBooking = async () => {
    // 1. Create booking (backend creates payment intent)
    const booking = await bookingAPI.createBooking({
      ride_id: ride.id,
      seats: selectedSeats,
    });

    // 2. Confirm payment with Stripe
    const { error, paymentIntent } = await confirmPayment(
      booking.client_secret,
      {
        paymentMethodType: 'Card',
      }
    );

    if (error) {
      Alert.alert('Payment Failed', error.message);
    } else {
      Alert.alert('Success', 'Ride booked!');
      navigation.navigate('MyBookings');
    }
  };
};
```

## Features:
- ✅ Seat selection with real-time availability
- ✅ Stripe payment integration
- ✅ Booking approval workflow (driver side)
- ✅ Booking history
- ✅ PDF receipt download
- ✅ Cancellation with refunds

---

<a name="tracking"></a>
# PART 7: REAL-TIME TRACKING

## WebSocket Integration

**File:** `src/services/websocket.ts`

```typescript
import io, { Socket } from 'socket.io-client';
import AsyncStorage from '@react-native-async-storage/async-storage';

class WebSocketService {
  private socket: Socket | null = null;

  async connect() {
    const token = await AsyncStorage.getItem('access_token');

    this.socket = io('ws://localhost:8005', {
      auth: { token },
      transports: ['websocket'],
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    this.socket.on('location_update', (data) => {
      // Handle location update
    });

    this.socket.on('trip_status', (data) => {
      // Handle trip status change
    });
  }

  joinTrip(tripId: string) {
    this.socket?.emit('join_trip', { trip_id: tripId });
  }

  updateLocation(lat: number, lng: number) {
    this.socket?.emit('update_location', { lat, lng });
  }

  disconnect() {
    this.socket?.disconnect();
  }
}

export const wsService = new WebSocketService();
```

## Features:
- ✅ Real-time driver location
- ✅ ETA updates
- ✅ Trip progress tracking
- ✅ Share trip link (safety feature)
- ✅ Geofencing notifications

---

<a name="ratings"></a>
# PART 8: RATINGS & REVIEWS

## Rate Ride Screen

```typescript
export const RateRideScreen = ({ route }: any) => {
  const { booking } = route.params;
  const [rating, setRating] = useState(5);
  const [review, setReview] = useState('');
  const [categoryRatings, setCategoryRatings] = useState({
    punctuality: 5,
    cleanliness: 5,
    communication: 5,
  });

  const handleSubmit = async () => {
    await ratingsAPI.createRating({
      booking_id: booking.id,
      rating,
      review,
      category_ratings: categoryRatings,
    });

    Alert.alert('Success', 'Rating submitted!');
    navigation.goBack();
  };

  return (
    <View>
      <StarRating rating={rating} onChange={setRating} />
      <CategoryRating
        category="Punctuality"
        rating={categoryRatings.punctuality}
        onChange={(val) => setCategoryRatings({...categoryRatings, punctuality: val})}
      />
      {/* ... other categories ... */}
      <TextInput
        label="Review (optional)"
        value={review}
        onChangeText={setReview}
        multiline
      />
      <Button onPress={handleSubmit}>Submit Rating</Button>
    </View>
  );
};
```

---

<a name="advanced"></a>
# PART 9: ADVANCED FEATURES

## Saved Locations

```typescript
export const SavedLocationsScreen = () => {
  const [locations, setLocations] = useState([]);

  useEffect(() => {
    loadSavedLocations();
  }, []);

  const loadSavedLocations = async () => {
    const data = await userAPI.getSavedLocations();
    setLocations(data);
  };

  const addLocation = async (location: SavedLocation) => {
    await userAPI.createSavedLocation(location);
    loadSavedLocations();
  };

  return (
    <View>
      <FlatList
        data={locations}
        renderItem={({ item }) => (
          <SavedLocationCard
            location={item}
            onDelete={() => deleteLocation(item.id)}
          />
        )}
      />
      <FAB onPress={() => navigation.navigate('AddSavedLocation')} />
    </View>
  );
};
```

## Driver Dashboard

```typescript
export const DriverDashboardScreen = () => {
  const [period, setPeriod] = useState('week');
  const [dashboard, setDashboard] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, [period]);

  const loadDashboard = async () => {
    const data = await bookingAPI.getDriverDashboard(period);
    setDashboard(data);
  };

  return (
    <ScrollView>
      {/* Earnings Card */}
      <Card>
        <Text variant="headlineMedium">
          ${dashboard?.earnings.net.toFixed(2)}
        </Text>
        <Text>Net Earnings ({period})</Text>
      </Card>

      {/* Statistics */}
      <Card>
        <Text>Total Rides: {dashboard?.statistics.total_rides}</Text>
        <Text>Completion Rate: {dashboard?.statistics.completion_rate}%</Text>
      </Card>

      {/* Upcoming Bookings */}
      <Text variant="titleLarge">Upcoming Bookings</Text>
      {/* ... */}
    </ScrollView>
  );
};
```

---

<a name="notifications"></a>
# PART 10: PUSH NOTIFICATIONS

## Firebase Setup

**File:** `src/services/notifications.ts`

```typescript
import messaging from '@react-native-firebase/messaging';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { userAPI } from '../api/users';

export const setupPushNotifications = async () => {
  // Request permission
  const authStatus = await messaging().requestPermission();
  const enabled =
    authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
    authStatus === messaging.AuthorizationStatus.PROVISIONAL;

  if (enabled) {
    // Get FCM token
    const token = await messaging().getToken();

    // Save to backend
    await userAPI.updateFCMToken(token);
    await AsyncStorage.setItem('fcm_token', token);
  }

  // Handle foreground messages
  messaging().onMessage(async (remoteMessage) => {
    console.log('Notification received:', remoteMessage);
    // Show in-app notification
  });

  // Handle background/quit state messages
  messaging().setBackgroundMessageHandler(async (remoteMessage) => {
    console.log('Background notification:', remoteMessage);
  });
};
```

---

<a name="sjsu"></a>
# PART 11: SJSU-SPECIFIC FEATURES

## Campus Locations Picker

```typescript
export const CampusLocationsScreen = ({ navigation, route }: any) => {
  const { onSelect } = route.params;
  const [locations, setLocations] = useState([]);
  const [category, setCategory] = useState('all');

  useEffect(() => {
    loadCampusLocations();
  }, [category]);

  const loadCampusLocations = async () => {
    const data = await sjsuAPI.getCampusLocations(category);
    setLocations(data.locations);
  };

  const handleSelect = (location: CampusLocation) => {
    onSelect({
      address: location.full_name,
      lat: location.lat,
      lng: location.lng,
    });
    navigation.goBack();
  };

  return (
    <View>
      {/* Category Filter */}
      <ScrollView horizontal>
        <Chip onPress={() => setCategory('all')}>All</Chip>
        <Chip onPress={() => setCategory('academic')}>Academic</Chip>
        <Chip onPress={() => setCategory('parking')}>Parking</Chip>
        <Chip onPress={() => setCategory('transit')}>Transit</Chip>
      </ScrollView>

      {/* Locations List */}
      <FlatList
        data={locations}
        renderItem={({ item }) => (
          <List.Item
            title={item.name}
            description={item.full_name}
            left={() => <Icon name={item.icon} size={24} />}
            onPress={() => handleSelect(item)}
          />
        )}
      />
    </View>
  );
};
```

## Event Rides

```typescript
export const EventRidesScreen = () => {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    loadUpcomingEvents();
  }, []);

  const loadUpcomingEvents = async () => {
    const data = await sjsuAPI.getUpcomingEvents();
    setEvents(data);
  };

  const viewEventRides = async (eventId: string) => {
    const rides = await sjsuAPI.getEventRides(eventId);
    navigation.navigate('RideSearch', { rides, event });
  };

  return (
    <FlatList
      data={events}
      renderItem={({ item }) => (
        <EventCard
          event={item}
          onViewRides={() => viewEventRides(item.id)}
        />
      )}
    />
  );
};
```

---

<a name="deployment"></a>
# PART 12: TESTING & DEPLOYMENT

## Testing Setup

```bash
# Install testing dependencies
npm install --save-dev @testing-library/react-native jest
npm install --save-dev @testing-library/jest-native

# Run tests
npm test
```

## iOS Deployment

```bash
# Build for App Store
cd ios
pod install
cd ..

# Open Xcode
open ios/SJSURideShare.xcworkspace

# Set signing & capabilities
# Archive & upload to App Store Connect
```

## Android Deployment

```bash
# Generate release APK
cd android
./gradlew assembleRelease

# Generate AAB (for Google Play)
./gradlew bundleRelease

# Upload to Google Play Console
```

## Environment Configuration

```typescript
// .env.production
API_BASE_URL=https://api.sjsurideshare.com
STRIPE_PUBLISHABLE_KEY=pk_live_...
GOOGLE_MAPS_API_KEY=AIza...
```

---

# COMPLETION CHECKLIST

## Core Features
- [ ] Authentication (login, register, logout)
- [ ] Profile management
- [ ] Email/Phone/SJSU verification
- [ ] Ride creation with maps
- [ ] Ride search with filters
- [ ] Saved locations
- [ ] Ride templates
- [ ] Booking with payment
- [ ] Real-time tracking
- [ ] Ratings & reviews
- [ ] Driver dashboard
- [ ] Push notifications
- [ ] Campus locations
- [ ] Event rides

## Testing
- [ ] Unit tests for utilities
- [ ] Component tests
- [ ] Integration tests
- [ ] E2E tests (Detox)
- [ ] Manual testing on iOS
- [ ] Manual testing on Android

## Deployment
- [ ] iOS App Store submission
- [ ] Android Play Store submission
- [ ] Environment variables configured
- [ ] API endpoints verified
- [ ] Push notifications working
- [ ] Deep linking configured
- [ ] Analytics integrated

---

# TIMELINE

**Week 14: Core Setup (5-7 days)**
- Project setup
- Navigation
- Authentication screens
- API integration

**Week 15: Ride Features (5-7 days)**
- Ride creation
- Ride search
- Google Maps integration
- Booking flow

**Week 16: Advanced Features (5-7 days)**
- Real-time tracking
- Payments
- Ratings
- Dashboard

**Week 17: Polish & Deploy (5-7 days)**
- SJSU features
- Push notifications
- Testing
- App Store submission

**Total: 3-4 weeks**

---

# COMPLETE PROMPT FOR CLAUDE CODE

```
PROJECT: SJSU RideShare - Section 14: React Native Mobile App

IMPLEMENT:

1. PROJECT SETUP:
   - Initialize React Native with TypeScript
   - Install all dependencies
   - Configure navigation
   - Set up Redux store

2. AUTHENTICATION:
   - Login/Register screens
   - API client with token management
   - Auth state management

3. PROFILE & VERIFICATION:
   - Profile screen with badges
   - Edit profile
   - Phone/Email/SJSU verification
   - Saved locations
   - Payment methods

4. RIDE FEATURES:
   - Create ride with Google Maps
   - Search rides with filters
   - Ride templates
   - Campus location picker
   - Booking flow with Stripe

5. REAL-TIME & ADVANCED:
   - WebSocket tracking
   - Rating system
   - Driver dashboard
   - Push notifications
   - Event rides

6. TESTING & DEPLOYMENT:
   - Unit tests
   - Build for iOS/Android
   - App Store submission

Use React Native best practices, TypeScript, and modern libraries.
Follow Material Design guidelines with react-native-paper.
```

---

**Next:** Section 15 - Comprehensive Testing & QA
