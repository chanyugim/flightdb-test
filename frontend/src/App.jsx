import { Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import RoundTrip from "./pages/RoundTrip";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import FlightDetail from "./pages/FlightDetail";
import Booking from "./pages/Booking";
import ReservationDetail from "./pages/ReservationDetail";
import MyPage from "./pages/MyPage";
import GuestLookup from "./pages/GuestLookup";
import Inquiry from "./pages/Inquiry";
import Admin from "./pages/Admin";
import Benefits from "./pages/Benefits";

export default function App() {
  return (
    <Routes>
      {/* 공통 레이아웃 안에서 URL별 화면을 연결함. */}
      <Route element={<Layout />}>
        <Route path="/" element={<Home />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/flights/:flightId" element={<FlightDetail />} />
        <Route path="/round-trip/:outboundId/:inboundId" element={<RoundTrip />} />
        <Route path="/booking" element={<Booking />} />
        <Route path="/reservations/:reservationNo" element={<ReservationDetail />} />
        <Route path="/guest/lookup" element={<GuestLookup />} />
        <Route path="/inquiry" element={<Inquiry />} />
        <Route path="/benefits" element={<Benefits />} />
        <Route
          path="/mypage"
          element={
            <ProtectedRoute>
              <MyPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute adminOnly>
              <Admin />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<p>페이지를 찾을 수 없습니다.</p>} />
      </Route>
    </Routes>
  );
}
