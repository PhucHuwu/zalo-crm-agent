import Link from "next/link";
export default function NotFound() { return <div className="not-found"><span className="eyebrow">Không tìm thấy bài viết</span><h1>Chúng ta quay lại nhé.</h1><p>Đường dẫn này chưa có hướng dẫn. Bạn có thể chọn một bài trong mục lục hoặc về trang tổng quan.</p><Link className="button button-primary" href="/">Về trang tổng quan</Link></div>; }
