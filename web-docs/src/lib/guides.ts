export type Section = {
  id: string;
  title: string;
  paragraphs?: string[];
  steps?: { title: string; body: string }[];
  note?: { title: string; body: string };
  prompt?: string;
  checks?: string[];
  faqs?: { question: string; answer: string }[];
};

export type Guide = {
  slug: string;
  title: string;
  shortTitle: string;
  /** Who acts in this step: the user on the computer, the user asking Claude, or both together. */
  actor: "Bạn làm trên máy" | "Bạn yêu cầu Claude" | "Bạn và Claude cùng làm";
  description: string;
  sections: Section[];
};

/** Step numbers match workflows/USER_GUIDE_FLOW.md so the site and Claude use the same numbers. */
export const cycle: Guide[] = [
  {
    slug: "mo-workflow", title: "Tải và mở workflow bằng Claude Code", shortTitle: "Tải & mở workflow", actor: "Bạn làm trên máy",
    description: "Tải ZIP từ GitHub, đặt tài liệu doanh nghiệp vào inputs, rồi mở thư mục trong Claude Desktop → tab Code. Cần gói Pro, Max, Team hoặc Enterprise.",
    sections: [
      { id: "download", title: "Tải workflow: Code → Download ZIP", paragraphs: ["Giải nén ra một thư mục, ví dụ zalo-crm-agent. Mỗi doanh nghiệp dùng một thư mục riêng, và mỗi OA chỉ chạy ở một thư mục, trên một máy."] },
      { id: "inputs", title: "Đặt tài liệu vào inputs", steps: [
        { title: "inputs/01_company_info", body: "Hồ sơ công ty, hồ sơ năng lực, khách hàng tiêu biểu." },
        { title: "inputs/02_marketing_materials", body: "Danh mục sản phẩm/dịch vụ, bảng giá, chính sách bán hàng, câu hỏi khách hay hỏi." }
      ], paragraphs: ["Ưu tiên PDF, Word, Excel có chữ. Ảnh scan có thể không đọc được. Chưa có tài liệu cũng được: ở bước 2 Claude có thể đọc website hoặc hỏi bạn từng câu."] },
      { id: "overview", title: "Mở Claude Desktop → tab Code" },
      { id: "folder", title: "Chọn thư mục workflow", paragraphs: ["Choose… → Open folder… → chọn thư mục zalo-crm-agent (thư mục có tệp CLAUDE.md). Chọn This computer, không chạy trên đám mây: khóa Zalo và TinaCRM chỉ nằm trên máy này."] },
      { id: "permissions", title: "Chọn quyền: Manual", steps: [
        { title: "Auto", body: "Claude tự quyết định việc nào cần hỏi. Không nên dùng khi mới bắt đầu." },
        { title: "Manual (nên chọn)", body: "Luôn hỏi bạn trước khi sửa tệp hoặc chạy lệnh." },
        { title: "Accept edits", body: "Tự sửa tệp không hỏi; chạy lệnh vẫn hỏi." },
        { title: "Plan", body: "Chỉ lập kế hoạch, chưa làm gì. Dùng khi muốn xem trước Claude định làm gì." },
        { title: "Bypass permissions (không dùng)", body: "Claude được sửa hoặc xóa tệp, gửi tin cho khách mà không hỏi." }
      ] },
      { id: "done", title: "Đã mở đúng", paragraphs: ["Thanh dưới ô nhập hiện This computer, tên thư mục workflow và Manual."], checks: ["Đã giải nén thư mục workflow", "Đã đặt tài liệu vào inputs (hoặc sẽ gửi website)", "Đang ở tab Code, đúng thư mục, quyền Manual"] }
    ]
  },
  {
    slug: "hieu-doanh-nghiep", title: "Claude hiểu doanh nghiệp", shortTitle: "Hiểu doanh nghiệp", actor: "Bạn yêu cầu Claude",
    description: "Claude đọc tài liệu, tóm tắt doanh nghiệp, rồi hỏi danh sách sản phẩm/dịch vụ và các nhóm khách bạn muốn phân loại.",
    sections: [
      { id: "send", title: "Câu lệnh", prompt: "Đọc CLAUDE.md và tài liệu trong inputs. Báo tệp nào không đọc được, tóm tắt doanh nghiệp và hỏi tôi phần còn thiếu." },
      { id: "why", title: "Vì sao cần bước này", paragraphs: ["Khi phân tích hội thoại, Claude dùng danh sách sản phẩm để biết khách đang hỏi mua gì, ước giá trị cơ hội. Danh sách nhóm khách (ví dụ khách nóng, khách đã mua, khách phàn nàn) dùng để lọc khách khi làm chiến dịch.", "Bạn duyệt bản tóm tắt, sản phẩm và nhóm khách. Sau này muốn sửa chỉ cần nhắn Claude, ví dụ “Thêm sản phẩm gói Premium giá 5 triệu”."] }
    ]
  },
  {
    slug: "khai-bao-oa", title: "Khai báo OA, ứng dụng và sale", shortTitle: "Khai báo OA & sale", actor: "Bạn yêu cầu Claude",
    description: "Mỗi OA có nhiều ứng dụng (tài khoản con). Mỗi ứng dụng giao cho một sale, và mỗi sale có một nhãn Zalo riêng để đánh dấu khách của mình.",
    sections: [
      { id: "concepts", title: "Ba khái niệm cần biết", steps: [
        { title: "OA (Official Account)", body: "Trang Zalo chính thức của doanh nghiệp, nơi khách nhắn tin." },
        { title: "Ứng dụng (tài khoản con)", body: "Tạo trên developers.zalo.me và được quản trị OA cấp quyền. Mỗi ứng dụng có App ID, Secret Key, và gắn với đúng một sale." },
        { title: "Nhãn sale", body: "Ví dụ “Sale: Minh”. Sale gắn nhãn này cho khách mình phụ trách trong OA Manager. Workflow dựa vào nhãn để biết khách thuộc sale nào." }
      ] },
      { id: "tags", title: "Vì sao phải dùng nhãn" },
      { id: "send", title: "Câu lệnh", paragraphs: ["Claude hỏi lần lượt: có mấy OA, mỗi OA có những ứng dụng nào (App ID, tên gợi nhớ), sale phụ trách (họ tên, email công ty), nhãn của sale, và người quản lý nhận khách chưa được giao. App ID không phải bí mật, có thể gửi trong chat."], prompt: "Khai báo OA, các ứng dụng và sale phụ trách. Hỏi tôi từng câu, rồi cho tôi xem bảng OA – ứng dụng – sale – nhãn để xác nhận." },
      { id: "no-app", title: "Chưa có ứng dụng?", paragraphs: ["Người quản trị OA vào developers.zalo.me → Tạo ứng dụng → chọn sản phẩm Official Account → liên kết OA → bật quyền quản lý tin nhắn người dùng, quản lý thông tin người dùng và quản lý thông tin OA (cần để gắn nhãn). Không chắc nút nào thì chụp màn hình gửi Claude, nhớ che thông tin nhạy cảm."] }
    ]
  },
  {
    slug: "ket-noi-zalo", title: "Kết nối Zalo", shortTitle: "Kết nối Zalo", actor: "Bạn và Claude cùng làm",
    description: "Với từng ứng dụng, người quản trị OA lấy Secret Key và Refresh Token rồi dán vào hộp thoại Claude bật lên. Không dán khóa vào khung chat.",
    sections: [
      { id: "token", title: "Lấy Refresh Token (API Explorer)", steps: [
        { title: "Mở công cụ", body: "Vào developers.zalo.me/tools/explorer, đăng nhập bằng tài khoản quản trị OA." },
        { title: "Chọn ứng dụng", body: "Chọn đúng ứng dụng của sale đang kết nối, loại OA Access Token." },
        { title: "Lấy token", body: "Bấm Lấy Access Token, cho phép, rồi sao chép Refresh Token." },
        { title: "Secret Key", body: "Ở trang ứng dụng trên developers.zalo.me, sao chép Khóa bí mật (Secret Key)." }
      ] },
      { id: "send", title: "Câu lệnh", prompt: "Kết nối Zalo cho từng ứng dụng đã khai báo. Bật hộp thoại để tôi dán Secret Key và Refresh Token, sau đó kiểm tra đúng OA và đọc thử, không in nội dung tin nhắn." },
      { id: "dialog", title: "Dán vào hộp thoại", paragraphs: ["Hộp thoại Kết nối Zalo OA hiện ra: dán Khóa bí mật, dán Refresh Token, bấm Lưu. Không thấy hộp thoại thì tìm trên thanh Dock (Mac) hoặc thanh tác vụ (Windows). Khóa chỉ được lưu khi Zalo chấp nhận.", "Claude báo tên OA nhận được và số hội thoại đọc được. Làm lần lượt cho mọi ứng dụng."] },
      { id: "tag-check", title: "Kiểm tra nhãn sale", paragraphs: ["Claude kiểm tra nhãn của từng sale đã có trên OA chưa. Nhãn chưa có không phải lỗi: Zalo tự tạo khi gắn cho khách đầu tiên."], prompt: "Kiểm tra nhãn sale của từng ứng dụng trên OA." },
      { id: "warn", title: "Lưu ý", note: { title: "Refresh Token chỉ dùng được một lần", body: "Mỗi lần làm mới, Zalo cấp token mới và workflow tự lưu lại. Vì vậy không dùng cùng một ứng dụng ở hai máy hoặc hai thư mục. Nếu ứng dụng không chạy quá khoảng 3 tháng, người quản trị OA phải cấp quyền lại." } }
    ]
  },
  {
    slug: "ket-noi-tinacrm", title: "Kết nối TinaCRM", shortTitle: "Kết nối TinaCRM", actor: "Bạn và Claude cùng làm",
    description: "Tạo API key trong TinaCRM, dán vào hộp thoại. Claude ghép từng sale với nhân viên CRM và ánh xạ giai đoạn cơ hội.",
    sections: [
      { id: "apikey-open", title: "Tạo API key", paragraphs: ["Đăng nhập TinaCRM của doanh nghiệp → Settings → MCP & APIs → tab API → Create API key."] },
      { id: "apikey-form", title: "Điền thông tin khóa", paragraphs: ["Role phải đủ quyền đọc/ghi People, Companies, Opportunities, Tasks và Notes. Nên đặt ngày hết hạn thay vì Never."] },
      { id: "apikey-copy", title: "Sao chép khóa", paragraphs: ["Khóa chỉ hiện một lần. Bấm Copy rồi gửi câu lệnh dưới đây. Không dán khóa vào khung chat."], prompt: "Kết nối TinaCRM bằng API key. Hỏi tôi địa chỉ TinaCRM, bật hộp thoại để tôi dán API key, sau đó đọc thử dữ liệu, chưa ghi gì." },
      { id: "apikey-paste", title: "Dán khóa vào hộp thoại", paragraphs: ["Claude bật hộp thoại Kết nối TinaCRM: dán khóa vào ô, bấm Lưu."] },
      { id: "mapping", title: "Ghép sale và giai đoạn", steps: [
        { title: "Sale ↔ nhân viên CRM", body: "Claude ghép theo email để task được giao đúng người. Không khớp thì Claude hỏi bạn." },
        { title: "Giai đoạn cơ hội", body: "Claude đọc các giai đoạn có trong CRM (ví dụ Mới, Báo giá, Thắng) và ghép với giai đoạn của workflow." },
        { title: "Trường Zalo trên People", body: "Nên có trường zalo_user_id để không tạo trùng khách, vì khách Zalo thường không để lại email hay điện thoại. Chưa có thì Claude hướng dẫn tạo." }
      ] }
    ]
  },
  {
    slug: "chay-thu", title: "Chạy thử ngày đầu", shortTitle: "Chạy thử ngày đầu", actor: "Bạn yêu cầu Claude",
    description: "Claude lấy hội thoại, phân tích, cho bạn xem mẫu và bảng sẽ tạo trên CRM. Chỉ đẩy lên CRM sau khi bạn duyệt.",
    sections: [
      { id: "send", title: "Câu lệnh", prompt: "Chạy thử hôm nay: lấy hội thoại, phân tích, cho tôi xem 3–5 bản phân tích mẫu và bảng sẽ tạo trên TinaCRM. Chưa ghi CRM khi tôi chưa duyệt." },
      { id: "what", title: "Claude tạo ra gì", steps: [
        { title: "People và Companies", body: "Khách và công ty của khách, kèm số điện thoại, email, địa chỉ nếu khách có nhắc trong chat." },
        { title: "Opportunities", body: "Cơ hội bán hàng: sản phẩm khách quan tâm, giá trị ước tính, giai đoạn." },
        { title: "Notes", body: "Tóm tắt hội thoại: khách cần gì, đã báo giá chưa, còn vướng gì." },
        { title: "Tasks", body: "Việc tiếp theo, giao cho sale có nhãn của khách. Khách chưa có nhãn thì giao cho người quản lý." }
      ] },
      { id: "flow", title: "Luồng dữ liệu" },
      { id: "review", title: "Duyệt và chạy thật", paragraphs: ["Xem bản phân tích có đúng ý khách không, sản phẩm và giá trị có hợp lý không. Chỉnh xong, nhắn “Đẩy lên CRM”. Claude báo số tạo mới, cập nhật, bỏ qua và lỗi thật trên TinaCRM.", "Khách có dấu hiệu bất thường (thông tin mâu thuẫn, khách có nhãn của hai sale) được đánh dấu cần xem lại và không tự đẩy lên CRM."] }
    ]
  },
  {
    slug: "hang-ngay", title: "Chạy hằng ngày và đặt lịch", shortTitle: "Chạy hằng ngày", actor: "Bạn yêu cầu Claude",
    description: "Sau lần chạy thử, mỗi ngày chỉ cần bước này. Mỗi sale nhận một brief việc cần làm hôm nay.",
    sections: [
      { id: "routine", title: "Câu lệnh", paragraphs: ["Claude chỉ lấy tin mới kể từ lần chạy trước. Chạy lại trong cùng ngày không tạo trùng."], prompt: "Chạy hôm nay." },
      { id: "one-sale", title: "Xem khách của một sale", prompt: "Khách của <tên sale> hôm nay." },
      { id: "assign", title: "Giao và chuyển khách", paragraphs: ["Tóm tắt mỗi ngày liệt kê khách chưa có nhãn sale. Cách tốt nhất là sale tự gắn nhãn của mình trong OA Manager (oa.zalo.me) khi nhận khách. Bạn cũng có thể nhờ Claude gắn: Claude cho xem danh sách trước, bạn duyệt mới gắn."], prompt: "Giao khách <tên khách> cho <tên sale>." },
      { id: "schedule", title: "Chạy tự động theo lịch", paragraphs: ["Claude hỏi giờ chạy (nên chọn 7:30 sáng ngày làm việc để sale có brief đầu ngày), và có tự đẩy CRM hay chờ bạn duyệt, rồi tự tạo lịch.", "Mỗi lần chạy hiện thành một phiên mới ở mục Scheduled bên trái. Lần đầu nếu ứng dụng hỏi quyền, bấm Always allow cho đúng các lệnh python3 scripts/… của workflow.", "Lịch chỉ chạy khi máy bật và Claude Desktop đang mở. Bỏ lỡ thì chạy bù khi mở lại, không mất tin."], prompt: "Đặt lịch chạy tự động hằng ngày." },
      { id: "outputs", title: "Kết quả nằm ở đâu" }
    ]
  },
  {
    slug: "chien-dich", title: "Tạo chiến dịch", shortTitle: "Tạo chiến dịch", actor: "Bạn yêu cầu Claude",
    description: "Dùng dữ liệu đã tích lũy để chọn nhóm khách: chốt khách nóng, đánh thức khách nguội, bán thêm, chăm sóc sau bán, giữ chân.",
    sections: [
      { id: "send", title: "Câu lệnh", paragraphs: ["Claude chỉ đề xuất loại chiến dịch đang có khách, kèm số khách theo từng sale và số khách còn nhắn được trên Zalo. Bạn điều chỉnh bộ lọc tới khi ưng."], prompt: "Tạo chiến dịch mới. Hỏi tôi mục tiêu, đề xuất nhóm khách dựa trên dữ liệu thật và cho tôi xem quy mô trước khi lưu." },
      { id: "types", title: "Loại chiến dịch gợi ý", steps: [
        { title: "Chốt khách nóng", body: "Khách hỏi giá, hẹn demo trong 7 ngày gần đây." },
        { title: "Đánh thức khách nguội", body: "Khách từng quan tâm nhưng im lặng hơn 14 ngày." },
        { title: "Bán thêm", body: "Khách đã mua, quan tâm sản phẩm liên quan." },
        { title: "Chăm sóc sau bán", body: "Khách mới mua trong 30 ngày: hướng dẫn dùng, xin đánh giá." },
        { title: "Giữ chân", body: "Khách phàn nàn hoặc có dấu hiệu rời bỏ: sale gọi trực tiếp." }
      ] },
      { id: "files", title: "Danh sách khách", paragraphs: ["Mỗi chiến dịch một thư mục campaigns/<tên chiến dịch>. Tệp outputs/audience.csv mở được bằng Excel để sale xem."] }
    ]
  },
  {
    slug: "kich-ban", title: "Kịch bản chăm sóc", shortTitle: "Kịch bản chăm sóc", actor: "Bạn yêu cầu Claude",
    description: "Claude soạn tin cá nhân hóa theo từng khách, gửi bằng ứng dụng của đúng sale phụ trách. Không gửi khi bạn chưa duyệt.",
    sections: [
      { id: "send", title: "Câu lệnh", prompt: "Soạn kịch bản chăm sóc cho chiến dịch <tên chiến dịch>: tin mẫu theo từng nhóm khách, cá nhân hóa theo hội thoại. Chưa gửi khi tôi chưa duyệt." },
      { id: "window", title: "Khung nhắn tự do của Zalo" },
      { id: "approve", title: "Cách duyệt", steps: [
        { title: "Chỉ soạn nháp", body: "Mặc định. Tin lưu thành tệp, sale tự sao chép gửi." },
        { title: "Duyệt từng tin", body: "Claude cho xem từng tin, bạn đồng ý mới gửi." },
        { title: "Duyệt mẫu rồi gửi loạt", body: "Duyệt mẫu và danh sách một lần, Claude gửi cho cả nhóm." }
      ], note: { title: "Khách yêu cầu ngừng liên hệ", body: "Khách nói không muốn nhận tin sẽ bị loại khỏi mọi chiến dịch sau đó." } },
      { id: "results", title: "Theo dõi kết quả", paragraphs: ["Lần chạy hằng ngày sau đó tự phân tích phản hồi của khách. Hỏi Claude “Kết quả chiến dịch <tên>” để xem đã gửi, đã trả lời, cơ hội mới."] }
    ]
  },
  {
    slug: "bao-cao", title: "Báo cáo tuần", shortTitle: "Báo cáo tuần", actor: "Bạn yêu cầu Claude",
    description: "Lượng hội thoại, khách mới, cơ hội, task, tốc độ phản hồi theo OA, ứng dụng và sale, cùng kết quả chiến dịch.",
    sections: [
      { id: "setup", title: "Câu lệnh", paragraphs: ["Claude hỏi người nhận, ngày và giờ gửi, cho xem bản nháp, rồi đặt lịch. Báo cáo lưu ở outputs/04_weekly_reports."], prompt: "Thiết lập báo cáo hằng tuần: hỏi tôi người nhận, ngày, giờ gửi, cho xem bản nháp rồi đặt lịch gửi tự động." },
      { id: "loop", title: "Sau bước 10", paragraphs: ["Mỗi ngày quay lại bước 7. Khi muốn chạy chiến dịch mới, quay lại bước 8."] }
    ]
  }
];

export const help: Guide = {
  slug: "tro-giup", title: "Câu hỏi thường gặp", shortTitle: "Câu hỏi thường gặp", actor: "Bạn yêu cầu Claude",
  description: "Các vướng mắc hay gặp.",
  sections: [
    { id: "faq", title: "Câu hỏi", faqs: [
      { question: "Mỗi ứng dụng có thấy riêng hội thoại của sale đó không?", answer: "Không. Zalo không tách hội thoại theo ứng dụng: mọi ứng dụng của cùng một OA đều thấy toàn bộ hội thoại. Vì vậy workflow dùng nhãn Zalo “Sale: <tên>” để biết khách thuộc ai." },
      { question: "Nhiều khách “chưa phân công”?", answer: "Sale chưa gắn nhãn cho khách. Nhắc sale gắn nhãn của mình trong OA Manager, hoặc nhắn Claude “Giao khách <tên> cho <sale>”. Trong lúc chờ, task CRM của các khách này giao cho người quản lý." },
      { question: "Khách có nhãn của hai sale?", answer: "Claude đánh dấu cần xem lại và hỏi bạn giữ sale nào, rồi gỡ nhãn sale kia." },
      { question: "Sale nghỉ việc, chuyển khách cho người khác?", answer: "Nhắn Claude “Đổi sale phụ trách ứng dụng <tên> thành <sale mới>”. Toàn bộ khách mang nhãn đó chuyển theo, không cần gắn lại." },
      { question: "Báo lỗi cần cấp quyền lại Zalo (reauthorize)?", answer: "Refresh Token đã hết hạn hoặc đã bị dùng ở nơi khác. Người quản trị OA lấy Refresh Token mới (bước 4) rồi nhắn “Kết nối lại ứng dụng <tên>”." },
      { question: "Không gửi được tin cho khách?", answer: "Zalo chỉ cho nhắn tự do trong khoảng 48 giờ sau tin cuối của khách. Ngoài khung, Claude tạo task để sale gọi hoặc nhắn trực tiếp." },
      { question: "Claude báo đã lưu nhưng TinaCRM không có?", answer: "Yêu cầu Claude kiểm tra lại bằng công cụ và báo ID bản ghi." },
      { question: "Lịch chạy không hoạt động?", answer: "Lịch chỉ chạy khi máy bật, không ngủ và Claude Desktop đang mở. Nếu phiên trong mục Scheduled đang chờ hỏi quyền, mở ra và bấm Always allow." },
      { question: "Đổi giờ, tạm dừng hoặc xem lịch?", answer: "Nhắn Claude, ví dụ “Xem các lịch đang chạy”, “Tạm dừng lịch hằng ngày”, “Đổi giờ chạy sang 8:00”." },
      { question: "Thêm sale hoặc ứng dụng mới?", answer: "Nhắn “Thêm ứng dụng mới cho sale <tên>”. Claude làm lại bước 3–5 chỉ cho ứng dụng đó." },
      { question: "Dùng trên hai máy được không?", answer: "Không dùng cùng một ứng dụng Zalo ở hai máy hoặc hai thư mục: token chỉ dùng được một lần nên máy kia sẽ bị từ chối. Dữ liệu chống trùng cũng chỉ nằm ở một thư mục." },
      { question: "Dùng cho doanh nghiệp khác?", answer: "Tải một bản workflow riêng và làm lại từ bước 1." }
    ] },
    { id: "privacy", title: "Dữ liệu khách hàng", paragraphs: ["Hội thoại, phân tích và khóa chỉ lưu trên máy này, trong thư mục workflow. Claude không in nội dung tin nhắn hay khóa ra khung chat khi không cần. Khi gửi ảnh chụp màn hình cho Claude, nhớ che khóa và thông tin khách."] },
    { id: "usage", title: "Xem mức sử dụng Claude", paragraphs: ["Bấm tên tài khoản ở góc dưới bên trái → Usage."] }
  ]
};

export type Phase = { id: string; title: string; when: string; from: number; to: number };

/** Groups of cycle steps (1-based, inclusive) so users can tell one-time setup from daily use. */
export const phases: Phase[] = [
  { id: "thiet-lap", title: "Thiết lập lần đầu", when: "Làm một lần cho mỗi doanh nghiệp.", from: 1, to: 5 },
  { id: "hang-ngay", title: "Dùng hằng ngày", when: "Thiết lập xong thì chỉ cần phần này. Claude có thể tự chạy theo lịch.", from: 6, to: 7 },
  { id: "chien-dich", title: "Chiến dịch & báo cáo", when: "Dùng dữ liệu đã tích lũy để bán hàng và chăm sóc khách.", from: 8, to: 10 }
];
export const phaseOf = (step: number) => phases.find((p) => step >= p.from && step <= p.to);

export const guides: Guide[] = [...cycle, help];
export const stepNumber = (slug: string) => cycle.findIndex((g) => g.slug === slug) + 1;
export const guideHref = (slug: string) => `/huong-dan/${slug}`;
