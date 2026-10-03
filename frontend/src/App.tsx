import { useEffect } from 'react'
import { BrowserRouter, Link, Route, Routes, useLocation } from 'react-router-dom'
import NavBar from './components/NavBar'
import Footer from './components/Footer'
import ChatBox from './components/ChatBox'
import Bulldog from './components/Bulldog'
import Home from './pages/Home'
import Products from './pages/Products'
import ProductDetail from './pages/ProductDetail'
import About from './pages/About'
import Login from './pages/Login'
import Signup from './pages/Signup'
import { BuddyResultsProvider } from './buddyResults'
import { AuthProvider } from './auth'

// New page = start at the top (React Router keeps the old scroll position otherwise).
function ScrollToTop() {
  const { pathname } = useLocation()
  useEffect(() => {
    // braces matter: newer Chrome returns a Promise from scrollTo, which React would treat as a cleanup
    window.scrollTo(0, 0)
  }, [pathname])
  return null
}

function NotFound() {
  return (
    <section className="section empty">
      <Bulldog size={140} />
      <h2>404: Buddy buried this page somewhere.</h2>
      <Link to="/" className="btn">Take me home</Link>
    </section>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <ScrollToTop />
      <AuthProvider>
        <BuddyResultsProvider>
          <NavBar />
          <main>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/products" element={<Products />} />
              <Route path="/products/:id" element={<ProductDetail />} />
              <Route path="/about" element={<About />} />
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="*" element={<NotFound />} />
            </Routes>
          </main>
          <Footer />
          <ChatBox />
        </BuddyResultsProvider>
      </AuthProvider>
    </BrowserRouter>
  )
}
