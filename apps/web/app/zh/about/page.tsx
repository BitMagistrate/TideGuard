import Link from "next/link";
import type { Metadata } from "next";
import ZhTranslationNotice from "../../../components/Lang/ZhTranslationNotice";

export const metadata: Metadata = {
  title: "創辦人故事 — Vladimir Ermolenko",
  description:
    "為什麼一位 17 歲、十年級的西伯利亞克拉斯諾亞爾斯克高中生在 3 個月內以 AI 編碼副駕駛協助建構了 TideGuard AI。第一人稱完整故事。",
  alternates: {
    canonical: "/zh/about",
    languages: { "en-US": "/about", "ru-RU": "/ru/about" },
  },
};

const CONTACT_EMAIL = "scaleblinkk@vk.com";
const GITHUB = "https://github.com/BitMagistrate/TideGuard";

export default function ZhAboutPage() {
  return (
    <main className="min-h-screen">
      <ZhTranslationNotice />

      {/* Hero */}
      <section className="bg-gradient-to-br from-teal-700 to-ocean-600 text-white">
        <div className="max-w-4xl mx-auto px-6 py-20">
          <p className="uppercase tracking-widest text-sand-100 text-xs mb-3">創辦人</p>
          <h1 className="text-4xl md:text-5xl font-bold leading-tight">
            我開始 TideGuard,是因為厭倦了在<em>退潮之後</em>才撿塑膠。
          </h1>
          <p className="text-lg text-sand-50 mt-6 max-w-2xl">
            Vladimir Ermolenko, 17 歲,第十三「Akadem」中學十年級,
            西伯利亞克拉斯諾亞爾斯克。創辦人 + AI 副駕駛。3 個月。放學後,一台筆電。
          </p>
        </div>
      </section>

      {/* Hard facts */}
      <section className="bg-sand-50 dark:bg-zinc-900/40 py-10">
        <div className="max-w-4xl mx-auto px-6 grid grid-cols-2 md:grid-cols-5 gap-4 text-center">
          <Fact label="年齡" value="17" />
          <Fact label="年級" value="十年級" />
          <Fact label="學校" value="第 13 中學" />
          <Fact label="城市" value="克拉斯諾亞爾斯克" />
          <Fact label="團隊" value="創辦人 + AI" />
        </div>
      </section>

      {/* Story */}
      <section className="max-w-3xl mx-auto px-6 py-16 prose dark:prose-invert prose-zinc">
        <p>
          我在 <strong>西伯利亞的克拉斯諾亞爾斯克</strong> 長大 ——
          距離最近的大海約 4 000 公里。每年夏天,我們全家會飛到南方的
          黑海海岸 —— 阿納帕、索契、克拉斯諾達爾邊疆區的海灣 ——
          每年夏天都是同樣的場景:第二天我手上就裝滿了瓶蓋、釣魚線、
          熔化的保麗龍碎片以及我無法完全辨識標籤的洗潔精瓶子。我以為
          是當地居民丟的。後來母親拿一個寫著羅馬尼亞文的塑膠水壺給我看,
          告訴我:多瑙河把整個黑海西半部的垃圾運過來,最後其中一部分
          沖到我們這邊。海灘上的髒亂與當地居民無關 —— 那是全球塑膠
          供應鏈的「會計錯誤」,最後落在我的腳邊。
        </p>
        <p>
          14 歲時我第一次參加正式的海岸淨灘。八小時工作,大約 100–200
          公斤的塑膠垃圾,一張學校證書,以及大約三週的自豪感 ——
          也就是下一場風暴又把同一段海灘重新填滿所需的時間。我問
          海洋學研究生主辦人:為什麼我們總是在塑膠垃圾沖上岸<em>之後</em>
          才出現,而不是<em>之前</em>?她平靜地告訴我:數學困難、
          資料散落在六個不同機構與三種語言之間、也沒人為漂浮垃圾建立
          公開、簡單、區域性的預報。我回家後開始閱讀文獻。
        </p>
        <p>
          我用免費的 YouTube 教學自學 Python。我第一個「預測器」是用
          垃圾數量對風速的線性迴歸,在第一次測試集就失敗。一年後,
          我讀到 Raissi、Perdikaris 與 Karniadakis 在 2019 年關於
          <strong>物理資訊神經網路</strong>的論文,意識到:同樣的方法
          可以從固體熱傳導方程式,轉到海洋。傳輸方程式是相同的:
          平流加擴散,再加一個項代表「擱淺」垃圾。缺的只是資料 ——
          令我驚訝的是,資料早已免費公開:Copernicus 海洋服務發布
          高解析度洋流,ECMWF 發布 ERA5 風場再分析,ESA Sentinel-2
          可以從太空看見漂浮的巨型塑膠。公民通報可以補足衛星看不到的縫隙。
        </p>
        <p>於是我建構了 <strong>TideGuard</strong>。</p>
        <p>
          我把它做成開源,因為下一個在另一片海灘的孩子不該等私人公司來
          賣他需要的東西。我做了教育模組,因為一個不培養下一位淨灘領袖
          的預測工具無法擴展到單一創辦人之外。我做了排行榜,因為我親眼
          看過 12 歲的孩子在一個學期內主辦<em>三場</em>社區淨灘 —— 只要
          班級儀表板上的數字在跳動。自豪感是可再生資源,而青少年特別
          擅長利用它。
        </p>
        <p>
          這不是我投到期刊的研究計畫。這是一個能用的工具。本儲存庫中的
          程式碼是用來部署、使用、拆解、改進並交給下一個學生接手的。
          程式 MIT 授權,內容 CC-BY-4.0;沒有專利,也沒有秘密。如果
          TideGuard 能讓任何一所學校多舉辦一次原本不會發生的淨灘 ——
          這個專案就已經回本。
        </p>
        <p>
          我 <strong>17 歲</strong>,<strong>十年級</strong>,就讀於
          <strong> 克拉斯諾亞爾斯克第 13「Akadem」中學</strong>。我在
          <strong> 三個月內</strong> 建構了 TideGuard,放學後與
          <strong> AI 編碼副駕駛</strong> 一起工作 —— 我指揮它、檢視它,
          並整合它的每一個輸出。每一個設計決策、每一個基準測試、每一行
          公開文案都是我的。我稱之為 <em>AI 輔助的單人創辦 (AI-augmented
          solo founding)</em>:我不是「一個人加一台筆電」,而是「一個人
          加上地球上最好的 LLM 工具」。我拒絕假裝不是。正因為如此,
          這個專案才能用三個月完成,而不是十八個月。我目前正在尋找
          1–2 位同齡共同負責人,以及海洋生物學或機器學習領域的學術導師。
          我不假設演算法能解決海洋污染,但我拒絕接受「<em>預測</em>是
          缺失環節」這個事實 —— 當免費的衛星就在我們頭頂、免費的 PyTorch
          就在筆電上時。我們可以在潮水<em>之前</em>到達海灘,而非之後。
          那就是擦地板與關水龍頭的差別。
        </p>
        <p>— <em>Vladimir Ermolenko</em> (Ермоленко Владимир Александрович), 創辦人</p>

        <h2>為什麼這個版本是誠實的</h2>
        <ul>
          <li>所有團隊成員姓名、學校與指標只以可驗證的形式陳述。任何
            尚未完成試點的數字,我們明確標示,而非編造。</li>
          <li>首頁沒有虛假的 KPI。網站讀取真實的 <code>/cleanups/stats</code>,
            計數為零時就顯示零。</li>
          <li>碳足跡數字標示為<em>估算值</em>,連結到訓練時實際的
            codecarbon 量測。</li>
          <li>PINN 相對於 persistence 的優勢以
            <code> apps/ml/benchmarks/latest.json</code> 的實際數字為準
            —— 看得見的誠實,勝過看不見的灌水。</li>
        </ul>
      </section>

      {/* CTA */}
      <section className="bg-teal-700 text-white py-14">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-2xl font-bold mb-3">支持 TideGuard,或只是來打聲招呼。</h2>
          <p className="text-sand-100 max-w-2xl mx-auto mb-6">
            我正在尋找學術導師 (海洋生物學家或機器學習研究員)、
            1–2 位同齡共同負責人,以及小額補助 (~$1 850 / 年) 來支付
            免費方案之外的主機費用,以及一趟到海岸的實地驗證旅行。
          </p>
          <div className="flex flex-wrap gap-3 justify-center">
            <a href={`mailto:${CONTACT_EMAIL}`} className="px-5 py-3 bg-white text-teal-700 font-semibold rounded-lg">
              寫信給我 — {CONTACT_EMAIL}
            </a>
            <a href={GITHUB} className="px-5 py-3 border border-white/30 rounded-lg hover:bg-white/10">
              GitHub 儲存庫
            </a>
            <Link href="/about" className="px-5 py-3 border border-white/30 rounded-lg hover:bg-white/10">
              English version
            </Link>
            <Link href="/ru/about" className="px-5 py-3 border border-white/30 rounded-lg hover:bg-white/10">
              Русская версия
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-zinc-200 dark:border-zinc-800 bg-white dark:bg-zinc-900 p-5">
      <div className="text-xs uppercase tracking-widest text-zinc-500">{label}</div>
      <div className="text-lg font-bold mt-1">{value}</div>
    </div>
  );
}
